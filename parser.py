from lexer import (Token, KEYWORD, ID, NUMBER, DATE, LBRACE, RBRACE, COLON, PERCENT, EOF,
                   PLUS, MINUS, STAR, SLASH, LPAREN, RPAREN, EQUAL,
                   GREATER, LESS, EQ, GEQ, LEQ, KEYWORDS)  # NOVOS TOKENS
from ast_nos import (NoProgramo, NoAtivo, NoPortfolio, NoSimular, NoRelatorio, NoComparar,
                     NoDefinir, NoSe, NoExprLogica, NoExprBinaria, NoExprUnaria, NoExprNumero, NoExprVar)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _atual(self):
        return self.tokens[self.pos]

    def _consumir(self, tipo_esperado, valor_esperado=None):
        tok = self._atual()
        if tok.tipo != tipo_esperado or (valor_esperado and tok.valor != valor_esperado):
            raise ErroSintatico(
                f"Linha {tok.linha}: esperado '{valor_esperado or tipo_esperado}' mas encontrado '{tok.valor}'.")
        self.pos += 1
        return tok

    def _verificar(self, tipo, valor=None):
        tok = self._atual()
        return tok.tipo == tipo and (valor is None or tok.valor == valor)

    def parsear(self):
        declaracoes = []
        while not self._verificar(EOF): declaracoes.append(self._declaracao())
        return NoProgramo(declaracoes)

    def _declaracao(self):
        tok = self._atual()
        if tok.tipo == KEYWORD:
            if tok.valor == 'ativo':      return self._decl_ativo()
            if tok.valor == 'portfolio':  return self._decl_portfolio()
            if tok.valor == 'simular':    return self._cmd_simular()
            if tok.valor == 'relatorio':  return self._cmd_relatorio()
            if tok.valor == 'comparar':   return self._cmd_comparar()
            if tok.valor == 'definir':    return self._cmd_definir()
            if tok.valor == 'se':         return self._cmd_se()  # ← NOVO
        raise ErroSintatico(f"Linha {tok.linha}: declaração inválida '{tok.valor}'.")

    #Comando Condicional SE
    def _cmd_se(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'se')
        condicao = self._expr_logica()
        self._consumir(KEYWORD, 'entao')

        comandos = []
        while not self._verificar(KEYWORD, 'fim') and not self._verificar(EOF):
            comandos.append(self._declaracao())

        self._consumir(KEYWORD, 'fim')
        return NoSe(condicao, comandos, linha)

    def _expr_logica(self):
        esq = self._expr()
        tok = self._atual()
        if tok.tipo in (EQ, GREATER, LESS, GEQ, LEQ):
            op = tok.valor
            self.pos += 1
            dir = self._expr()
            return NoExprLogica(esq, op, dir)
        raise ErroSintatico(f"Linha {tok.linha}: esperada operação lógica (==, >, <, >=, <=).")

    #Outros Comandos
    def _cmd_definir(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'definir')
        nome = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(EQUAL)
        return NoDefinir(nome, self._expr(), linha)

    def _decl_ativo(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'ativo')
        nome = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(LBRACE)

        tipo = self._campo_keyword('tipo')
        quantidade = self._campo_expr('quantidade')
        preco_medio = self._campo_expr('preco_medio')

        taxa, vencimento, indexador, aporte_mensal = None, None, None, NoExprNumero(0.0)

        while not self._verificar(RBRACE):
            tok = self._atual()
            if tok.valor == 'taxa':
                taxa = self._campo_taxa_expr()
            elif tok.valor == 'vencimento':
                vencimento = self._campo_data('vencimento')
            elif tok.valor == 'indexador':
                indexador = self._campo_keyword('indexador')
            elif tok.valor == 'aporte_mensal':
                aporte_mensal = self._campo_expr('aporte_mensal')  # ← NOVO
            else:
                raise ErroSintatico(f"Linha {tok.linha}: campo inesperado '{tok.valor}'.")

        self._consumir(RBRACE)
        return NoAtivo(nome, tipo, quantidade, preco_medio, taxa, vencimento, indexador, aporte_mensal, linha)

    def _campo_keyword(self, n):
        self._consumir(KEYWORD, n); self._consumir(COLON); return self._consumir(KEYWORD).valor

    def _campo_expr(self, n):
        self._consumir(KEYWORD, n); self._consumir(COLON); return self._expr()

    def _campo_taxa_expr(self):
        self._consumir(KEYWORD, 'taxa'); self._consumir(COLON); e = self._expr(); self._consumir(PERCENT); return e

    def _campo_data(self, n):
        self._consumir(KEYWORD, n); self._consumir(COLON); return self._consumir(DATE).valor

    def _decl_portfolio(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'portfolio')
        nome = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(LBRACE)
        ativos = []
        while not self._verificar(RBRACE):
            self._consumir(KEYWORD, 'ativo');
            self._consumir(COLON)
            ativos.append(self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor)
        self._consumir(RBRACE)
        return NoPortfolio(nome, ativos, linha)

    def _cmd_simular(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'simular')
        nome = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(KEYWORD, 'periodo');
        self._consumir(COLON)
        e = self._expr();
        self._consumir(KEYWORD, 'meses')
        return NoSimular(nome, e, linha)

    def _cmd_relatorio(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'relatorio')
        nome = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(KEYWORD, 'rentabilidade')
        return NoRelatorio(nome, linha)

    def _cmd_comparar(self):
        linha = self._atual().linha
        self._consumir(KEYWORD, 'comparar')
        na = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        self._consumir(KEYWORD, 'com')
        nb = self._consumir(ID).valor if self._atual().tipo == ID else self._consumir(KEYWORD).valor
        return NoComparar(na, nb, linha)

    def _expr(self):
        esq = self._termo()
        while self._atual().tipo in (PLUS, MINUS):
            op = self._atual().valor;
            self.pos += 1
            esq = NoExprBinaria(op, esq, self._termo())
        return esq

    def _termo(self):
        esq = self._fator()
        while self._atual().tipo in (STAR, SLASH):
            op = self._atual().valor;
            self.pos += 1
            esq = NoExprBinaria(op, esq, self._fator())
        return esq

    def _fator(self):
        tok = self._atual()
        if tok.tipo == PLUS: self.pos += 1; return NoExprUnaria('+', self._fator())
        if tok.tipo == MINUS: self.pos += 1; return NoExprUnaria('-', self._fator())
        if tok.tipo == NUMBER: self.pos += 1; return NoExprNumero(tok.valor)
        if tok.tipo == LPAREN:
            self.pos += 1;
            e = self._expr();
            self._consumir(RPAREN);
            return e

        reservadas = KEYWORDS
        if tok.tipo == ID or (tok.tipo == KEYWORD and tok.valor not in reservadas):
            self.pos += 1;
            return NoExprVar(tok.valor)
        raise ErroSintatico(f"Linha {tok.linha}: fator inválido '{tok.valor}'.")


class ErroSintatico(Exception): pass