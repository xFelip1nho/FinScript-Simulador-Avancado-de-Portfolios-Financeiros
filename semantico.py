from datetime import date
from ast_nos import (NoProgramo, NoAtivo, NoPortfolio, NoSimular,
                     NoRelatorio, NoComparar, NoDefinir, NoSe,
                     NoExprBinaria, NoExprUnaria, NoExprNumero, NoExprVar)

LIMIAR_CONCENTRACAO = 0.80


class AnalisadorSemantico:
    def __init__(self):
        self.tabela = {}
        self.variaveis = {}
        self.alertas = []

    def analisar(self, programa):
        self._analisar_bloco(programa.declaracoes)

    def _analisar_bloco(self, declaracoes):
        for no in declaracoes:
            if isinstance(no, NoDefinir):
                self._analisar_definir(no)
            elif isinstance(no, NoAtivo):
                self._analisar_ativo(no)
            elif isinstance(no, NoPortfolio):
                self._analisar_portfolio(no)
            elif isinstance(no, NoSimular):
                self._analisar_simular(no)
            elif isinstance(no, NoRelatorio):
                self._analisar_relatorio(no)
            elif isinstance(no, NoComparar):
                self._analisar_comparar(no)
            elif isinstance(no, NoSe):
                self._analisar_se(no)

    def avaliar_expr(self, no):
        if isinstance(no, (int, float)): return float(no)
        if isinstance(no, NoExprNumero): return no.valor
        if isinstance(no, NoExprVar):
            if no.nome not in self.variaveis: raise ErroSemantico(f"Variável '{no.nome}' não declarada com 'definir'.")
            return self.variaveis[no.nome]
        if isinstance(no, NoExprUnaria):
            val = self.avaliar_expr(no.operando)
            return -val if no.op == '-' else val
        if isinstance(no, NoExprBinaria):
            esq, dir = self.avaliar_expr(no.esq), self.avaliar_expr(no.dir)
            if no.op == '+': return esq + dir
            if no.op == '-': return esq - dir
            if no.op == '*': return esq * dir
            if no.op == '/':
                if dir == 0: raise ErroSemantico("Divisão por zero.")
                return esq / dir

    def _analisar_definir(self, no):
        # Permite redefinição de variáveis: útil quando dois blocos 'se' mutuamente
        # exclusivos definem a mesma variável com valores diferentes.
        self.variaveis[no.nome] = self.avaliar_expr(no.expr)

    #Análise Condicional (Se)
    def _analisar_se(self, no):
        esq = self.avaliar_expr(no.condicao.esq)
        dir = self.avaliar_expr(no.condicao.dir)
        op = no.condicao.op

        if op == '==':
            res = esq == dir
        elif op == '>':
            res = esq > dir
        elif op == '<':
            res = esq < dir
        elif op == '>=':
            res = esq >= dir
        elif op == '<=':
            res = esq <= dir
        else:
            res = False

        no.resultado_avaliado = res

        # Só analisa os comandos internos se a condição for verdadeira.
        # Isso evita que ativos/portfólios dentro de um bloco falso sejam
        # registrados na tabela de símbolos e executados indevidamente.
        if res:
            self._analisar_bloco(no.comandos)

    def _analisar_ativo(self, no):
        if no.nome in self.tabela: raise ErroSemantico(f"Linha {no.linha}: '{no.nome}' já declarado.")
        no.quantidade = self.avaliar_expr(no.quantidade)
        no.preco_medio = self.avaliar_expr(no.preco_medio)
        no.aporte_mensal = self.avaliar_expr(no.aporte_mensal) if no.aporte_mensal else 0.0
        if no.taxa is not None: no.taxa = self.avaliar_expr(no.taxa)

        self.tabela[no.nome] = {'categoria': 'ativo', 'no': no}
        self._verificar_campos_por_tipo(no)
        self._verificar_valores_numericos(no)
        if no.vencimento: self._verificar_data(no.vencimento, no.nome, no.linha)

    def _verificar_campos_por_tipo(self, no):
        tipo = no.tipo
        if tipo == 'renda_fixa':
            if no.taxa is None: raise ErroSemantico(f"Linha {no.linha}: '{no.nome}' exige taxa.")
            if no.indexador is None: raise ErroSemantico(f"Linha {no.linha}: '{no.nome}' exige indexador.")
            if no.vencimento is None: raise ErroSemantico(f"Linha {no.linha}: '{no.nome}' exige vencimento.")
        elif tipo == 'acao':
            if no.taxa is not None or no.indexador is not None:
                self._alerta(f"Linha {no.linha}: 'taxa/indexador' ignorados em 'acao' ('{no.nome}').")

        if no.indexador in ('CDI', 'IPCA', 'SELIC') and tipo != 'renda_fixa':
            raise ErroSemantico(f"Linha {no.linha}: indexador '{no.indexador}' é apenas para renda_fixa.")

    def _verificar_valores_numericos(self, no):
        if no.quantidade <= 0 or no.quantidade != int(no.quantidade):
            raise ErroSemantico(
                f"Linha {no.linha}: 'quantidade' deve ser um número inteiro positivo (ex: 10). "
                f"Valor recebido: {no.quantidade}.")
        if no.preco_medio <= 0: raise ErroSemantico(f"Linha {no.linha}: 'preco_medio' deve ser > 0.")
        if no.aporte_mensal < 0: raise ErroSemantico(f"Linha {no.linha}: 'aporte_mensal' não pode ser negativo.")
        if no.taxa is not None and no.taxa < 0: raise ErroSemantico(f"Linha {no.linha}: 'taxa' não pode ser negativa.")

    def _verificar_data(self, data_str, nome_ativo, linha):
        try:
            d, m, a = map(int, data_str.split('/'))
            if date(a, m, d) <= date.today():
                self._alerta(f"Linha {linha}: ativo '{nome_ativo}' vencido ({data_str}).")
        except ValueError:
            raise ErroSemantico(f"Linha {linha}: data inválida.")

    def _analisar_portfolio(self, no):
        if no.nome in self.tabela: raise ErroSemantico(f"Linha {no.linha}: '{no.nome}' já declarado.")
        for nome_ativo in no.ativos:
            if nome_ativo not in self.tabela or self.tabela[nome_ativo]['categoria'] != 'ativo':
                raise ErroSemantico(f"Linha {no.linha}: '{nome_ativo}' inválido/não declarado.")
        self.tabela[no.nome] = {'categoria': 'portfolio', 'no': no}

    def _verificar_eh_portfolio(self, nome, linha):
        if nome not in self.tabela or self.tabela[nome]['categoria'] != 'portfolio': raise ErroSemantico(
            f"Linha {linha}: '{nome}' não é portfólio.")

    def _analisar_simular(self, no):
        self._verificar_eh_portfolio(no.nome_portfolio, no.linha)
        no.periodo = int(round(self.avaliar_expr(no.periodo)))
        if no.periodo <= 0: raise ErroSemantico(f"Linha {no.linha}: período <= 0.")

    def _analisar_relatorio(self, no):
        self._verificar_eh_portfolio(no.nome_portfolio, no.linha)

    def _analisar_comparar(self, no):
        self._verificar_eh_portfolio(no.nome_a, no.linha); self._verificar_eh_portfolio(no.nome_b, no.linha)

    def _alerta(self, msg):
        self.alertas.append(f"[AVISO SEMÂNTICO] {msg}")


class ErroSemantico(Exception): pass