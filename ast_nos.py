# FINSCRIPT - NÓS DA AST (Árvore Sintática Abstrata)

class NoProgramo:
    def __init__(self, declaracoes):
        self.declaracoes = declaracoes

class NoAtivo:
    def __init__(self, nome, tipo, quantidade, preco_medio,
                 taxa=None, vencimento=None, indexador=None, aporte_mensal=0.0, linha=None):
        self.nome          = nome
        self.tipo          = tipo
        self.quantidade    = quantidade
        self.preco_medio   = preco_medio
        self.taxa          = taxa
        self.vencimento    = vencimento
        self.indexador     = indexador
        self.aporte_mensal = aporte_mensal # ← NOVO: Fase 2
        self.linha         = linha

class NoPortfolio:
    def __init__(self, nome, ativos, linha=None):
        self.nome   = nome
        self.ativos = ativos
        self.linha  = linha

class NoSimular:
    def __init__(self, nome_portfolio, periodo, linha=None):
        self.nome_portfolio = nome_portfolio
        self.periodo        = periodo
        self.linha          = linha

class NoRelatorio:
    def __init__(self, nome_portfolio, linha=None):
        self.nome_portfolio = nome_portfolio
        self.linha          = linha

class NoComparar:
    def __init__(self, nome_a, nome_b, linha=None):
        self.nome_a = nome_a
        self.nome_b = nome_b
        self.linha  = linha

class NoDefinir:
    def __init__(self, nome, expr, linha=None):
        self.nome  = nome
        self.expr  = expr
        self.linha = linha

# ── NOVOS NÓS: Fase 3 (Condicionais) ──────────────────────────────────────────

class NoSe:
    """Bloco condicional: se <condicao> entao <comandos> fim"""
    def __init__(self, condicao, comandos, linha=None):
        self.condicao = condicao
        self.comandos = comandos
        self.linha = linha
        self.resultado_avaliado = False # Preenchido no semântico

class NoExprLogica:
    """Expressão booleana: esq ==, >, <, >=, <= dir"""
    def __init__(self, esq, op, dir):
        self.esq = esq
        self.op  = op
        self.dir = dir

# ── Nós Matemáticos ───────────────────────────────────────────────────────────

class NoExprBinaria:
    def __init__(self, op, esq, dir):
        self.op  = op
        self.esq = esq
        self.dir = dir

class NoExprUnaria:
    def __init__(self, op, operando):
        self.op       = op
        self.operando = operando

class NoExprNumero:
    def __init__(self, valor):
        self.valor = float(valor)

class NoExprVar:
    def __init__(self, nome):
        self.nome = nome