# FINSCRIPT - INTERPRETADOR

from ast_nos import (NoProgramo, NoAtivo, NoPortfolio, NoSimular,
                     NoRelatorio, NoComparar, NoDefinir, NoSe)

# Taxas de referência do mercado brasileiro utilizadas nas simulações.
# Fonte: Banco Central do Brasil / ANBIMA (valores de referência para fins acadêmicos).
# Em um sistema de produção, esses valores seriam obtidos via API (ex: api.bcb.gov.br).
TAXA_CDI_ANUAL    = 10.65   # CDI médio anual estimado (% a.a.)
TAXA_SELIC_ANUAL  = 10.75   # Meta Selic vigente (% a.a.)
TAXA_IPCA_ANUAL   =  4.83   # IPCA acumulado 12 meses (% a.a.)
RENDIMENTO_ACAO   = 12.0    # Rendimento médio histórico de ações (% a.a.)
RENDIMENTO_FUNDO  =  9.0    # Rendimento padrão de fundos sem taxa declarada (% a.a.)


class Interpretador:
    def __init__(self, tabela_simbolos):
        self.tabela = tabela_simbolos
        self.dados_grafico = {}

    def executar(self, programa_ou_lista):
        declaracoes = programa_ou_lista if isinstance(programa_ou_lista, list) else programa_ou_lista.declaracoes
        for no in declaracoes:
            if isinstance(no, NoSe):
                if getattr(no, 'resultado_avaliado', False):
                    self.executar(no.comandos)
            elif isinstance(no, NoSimular):
                self._executar_simular(no)
            elif isinstance(no, NoRelatorio):
                self._executar_relatorio(no)
            elif isinstance(no, NoComparar):
                self._executar_comparar(no)


    # SIMULAÇÃO INDIVIDUAL (COM HISTÓRICO MÊS A MÊS PARA GRÁFICO DE LINHA)
    def _executar_simular(self, no):
        portfolio_no = self.tabela[no.nome_portfolio]['no']
        meses = no.periodo

        print("=" * 70)
        print(f"  SIMULAÇÃO: {no.nome_portfolio.upper()}")
        print(f"  Período:   {meses} meses")
        print("=" * 70)

        vi_total = 0.0
        vf_total = 0.0
        total_aportado = 0.0
        imposto_total = 0.0

        historico_portfolio = [0.0] * (meses + 1)

        for nome_ativo in portfolio_no.ativos:
            ativo = self.tabela[nome_ativo]['no']
            vi, vf_liq, imposto, hist_ativo, t_inv = self._simular_ativo(ativo, meses)
            vi_total += vi
            vf_total += vf_liq
            total_aportado += (t_inv - vi)
            imposto_total += imposto

            for i in range(meses + 1):
                historico_portfolio[i] += hist_ativo[i]

            lucro = vf_liq - t_inv
            pct = (lucro / t_inv * 100) if t_inv else 0

            print(f"\n  Ativo: {nome_ativo}")
            print(f"    Tipo:                  {ativo.tipo}")
            print(f"    Investimento Inicial:  R$ {vi:>12,.2f}")
            if getattr(ativo, 'aporte_mensal', 0) > 0:
                print(f"    Aportes Acumulados:    R$ {(t_inv - vi):>12,.2f} ({ativo.aporte_mensal:.2f}/mês)")
            if imposto > 0:
                print(f"    Imposto Retido (IR):   R$ {imposto:>12,.2f}")
            print(f"    Valor Final Líquido:   R$ {vf_liq:>12,.2f}")
            print(f"    Rentab. Líquida:       {pct:+.2f}%")

        self.dados_grafico[no.nome_portfolio] = {
            "tipo": "line",
            "labels": [f"Mês {i}" for i in range(meses + 1)],
            "data": [round(x, 2) for x in historico_portfolio]
        }

        total_investido = vi_total + total_aportado
        ganho = vf_total - total_investido
        ganho_pct = (ganho / total_investido * 100) if total_investido else 0

        print("\n" + "-" * 70)
        print(f"  TOTAL PORTFÓLIO")
        print(f"    Valor inicial:     R$ {vi_total:>12,.2f}")
        print(f"    Aportes (Total):   R$ {total_aportado:>12,.2f}")
        print(f"    Total Investido:   R$ {total_investido:>12,.2f}")
        print(f"    Total IR Retido:   R$ {imposto_total:>12,.2f}")
        print(f"    VALOR LÍQUIDO:     R$ {vf_total:>12,.2f}")
        print(f"    Lucro Líquido Real:R$ {ganho:>12,.2f}  ({ganho_pct:+.2f}%)")
        print("-" * 70)

        # --- INÍCIO DA LEGENDA ADICIONADA ---
        print(f"  * LEGENDA INFORMATIVA:")
        print(f"    - IR: Imposto de Renda regressivo retido exclusivamente sobre o lucro (Renda Fixa).")
        print(f"    - Lucro Líquido Real: Montante final de ganho já descontando depósitos extras e impostos.")
        # --- FIM DA LEGENDA ---

        print("=" * 70)
        print()

    def _simular_ativo(self, ativo, meses):
        vi = ativo.quantidade * ativo.preco_medio
        aporte = getattr(ativo, 'aporte_mensal', 0.0)
        taxa_anual = self._taxa_anual_efetiva(ativo)
        taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1

        vf = vi
        historico = [vi]

        for _ in range(meses):
            vf = (vf * (1 + taxa_mensal)) + aporte
            historico.append(vf)

        total_investido = vi + (aporte * meses)
        lucro_bruto = vf - total_investido
        imposto = 0.0

        if ativo.tipo == 'renda_fixa' and lucro_bruto > 0:
            if meses <= 6:
                imposto = lucro_bruto * 0.225
            elif meses <= 12:
                imposto = lucro_bruto * 0.20
            elif meses <= 24:
                imposto = lucro_bruto * 0.175
            else:
                imposto = lucro_bruto * 0.15

        vf_liquido = vf - imposto
        historico[-1] = vf_liquido
        return vi, vf_liquido, imposto, historico, total_investido

    def _taxa_anual_efetiva(self, ativo):
        if ativo.tipo == 'renda_fixa':
            idx = ativo.indexador
            taxa = ativo.taxa
            if idx == 'CDI':       return (taxa / 100) * TAXA_CDI_ANUAL
            if idx == 'SELIC':     return (taxa / 100) * TAXA_SELIC_ANUAL
            if idx == 'IPCA':      return TAXA_IPCA_ANUAL + taxa
            if idx == 'prefixado': return taxa
            return taxa
        if ativo.tipo == 'acao':
            return RENDIMENTO_ACAO
        if ativo.tipo == 'fundo':
            if ativo.taxa is None:
                return RENDIMENTO_FUNDO
            # Convenção: taxa > 30 é interpretada como % do CDI (ex: 110 = 110% CDI).
            # Taxa <= 30 é interpretada como taxa anual direta em % a.a. (ex: 9.5 = 9.5% a.a.).
            # Isso espelha a mesma lógica usada em renda_fixa com indexador CDI.
            if ativo.taxa > 30:
                return (ativo.taxa / 100) * TAXA_CDI_ANUAL
            return ativo.taxa
        return 0.0

    # RELATÓRIO
    def _executar_relatorio(self, no):
        portfolio_no = self.tabela[no.nome_portfolio]['no']

        print("=" * 60)
        print(f"  RELATÓRIO DE RENTABILIDADE: {no.nome_portfolio.upper()}")
        print("=" * 60)

        valor_total = 0.0
        linhas_ativos = []

        for nome_ativo in portfolio_no.ativos:
            ativo = self.tabela[nome_ativo]['no']
            valor = ativo.quantidade * ativo.preco_medio
            taxa_anual = self._taxa_anual_efetiva(ativo)
            valor_total += valor
            linhas_ativos.append((nome_ativo, ativo, valor, taxa_anual))

        print(f"\n  {'Ativo':<22} {'Tipo':<12} {'Valor (R$)':>13} "
              f"{'% Carteira':>10} {'Taxa a.a.':>10}")
        print(f"  {'-' * 22} {'-' * 12} {'-' * 13} {'-' * 10} {'-' * 10}")

        for nome_ativo, ativo, valor, taxa_anual in linhas_ativos:
            pct = (valor / valor_total * 100) if valor_total else 0
            print(f"  {nome_ativo:<22} {ativo.tipo:<12} "
                  f"{valor:>13,.2f} {pct:>9.1f}% {taxa_anual:>9.2f}%")

        print(f"  {'-' * 22} {'-' * 12} {'-' * 13} {'-' * 10} {'-' * 10}")
        print(f"  {'TOTAL':<22} {'':<12} {valor_total:>13,.2f} {'100.0%':>10}")
        print("-" * 60)

        # --- INÍCIO DA LEGENDA ADICIONADA ---
        print(f"  * LEGENDA INFORMATIVA:")
        print(f"    - a.a.: Significa 'ao ano', que é a rentabilidade estimada para 12 meses.")
        print(f"    - % Carteira: Representa a concentração de risco do ativo no portfólio.")
        # --- FIM DA LEGENDA ---

        print("=" * 60)
        print()

    # COMPARAÇÃO (COM HISTÓRICO E EXPORTAÇÃO PARA GRÁFICO DE PIZZA)

    def _executar_comparar(self, no):
        port_a = self.tabela[no.nome_a]['no']
        port_b = self.tabela[no.nome_b]['no']
        MESES = 12

        print("=" * 60)
        print(f"  COMPARAÇÃO: {no.nome_a.upper()} vs {no.nome_b.upper()}")
        print(f"  Horizonte:  {MESES} meses")
        print("=" * 60)

        def resumo(port_no):
            vi_t = vf_t = t_inv = 0.0
            for nome in port_no.ativos:
                ativo = self.tabela[nome]['no']
                vi, vf, _, _, inv = self._simular_ativo(ativo, MESES)
                vi_t += vi
                vf_t += vf
                t_inv += inv
            pct = (vf_t - t_inv) / t_inv * 100 if t_inv else 0
            return t_inv, vf_t, pct

        inv_a, vf_a, g_a = resumo(port_a)
        inv_b, vf_b, g_b = resumo(port_b)

        print(f"\n  {'Portfólio':<28} {'Total Investido':>16} "
              f"{'Valor Líquido':>16} {'Rentabilidade':>14}")
        print(f"  {'-' * 28} {'-' * 16} {'-' * 16} {'-' * 14}")
        print(f"  {no.nome_a:<28} {inv_a:>16,.2f} {vf_a:>16,.2f} {g_a:>13.2f}%")
        print(f"  {no.nome_b:<28} {inv_b:>16,.2f} {vf_b:>16,.2f} {g_b:>13.2f}%")
        print()

        if g_a > g_b:
            print(f"  >> '{no.nome_a}' supera '{no.nome_b}' em {g_a - g_b:.2f} p.p. no período.")
        elif g_b > g_a:
            print(f"  >> '{no.nome_b}' supera '{no.nome_a}' em {g_b - g_a:.2f} p.p. no período.")
        else:
            print(f"  >> Desempenho equivalente.")

        print("-" * 60)

        # --- INÍCIO DA LEGENDA ADICIONADA ---
        print(f"  * LEGENDA INFORMATIVA:")
        print(f"    - p.p.: Pontos Percentuais (a diferença matemática direta entre as duas taxas).")
        print(f"    - Valor Líquido: O montante final projetado com os impostos já descontados.")
        # --- FIM DA LEGENDA ---

        print("=" * 60)
        print()

        self.dados_grafico["comparacao"] = {
            "tipo": "pie",
            "labels": [no.nome_a.upper(), no.nome_b.upper()],
            "data": [round(vf_a, 2), round(vf_b, 2)]
        }