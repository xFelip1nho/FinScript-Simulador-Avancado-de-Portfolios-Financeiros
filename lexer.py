import re

KEYWORD  = 'KEYWORD'
ID       = 'ID'
NUMBER   = 'NUMBER'
DATE     = 'DATE'
LBRACE   = 'LBRACE'
RBRACE   = 'RBRACE'
COLON    = 'COLON'
PERCENT  = 'PERCENT'
PLUS     = 'PLUS'
MINUS    = 'MINUS'
STAR     = 'STAR'
SLASH    = 'SLASH'
LPAREN   = 'LPAREN'
RPAREN   = 'RPAREN'
EQUAL    = 'EQUAL'
GREATER  = 'GREATER' # >
LESS     = 'LESS'    # <
EQ       = 'EQ'      # ==
GEQ      = 'GEQ'     # >=
LEQ      = 'LEQ'     # <=
EOF      = 'EOF'

KEYWORDS = {
    'ativo', 'portfolio', 'simular', 'relatorio', 'comparar',
    'tipo', 'quantidade', 'preco_medio', 'taxa', 'vencimento',
    'indexador', 'periodo', 'meses', 'rentabilidade', 'com',
    'renda_fixa', 'acao', 'fundo',
    'CDI', 'IPCA', 'SELIC', 'prefixado',
    'definir', 'aporte_mensal', 'se', 'entao', 'fim'
}

class Token:
    def __init__(self, tipo, valor, linha):
        self.tipo  = tipo
        self.valor = valor
        self.linha = linha
    def __repr__(self):
        return f'Token({self.tipo}, {repr(self.valor)}, linha={self.linha})'

class Lexer:
    def __init__(self, texto):
        self.texto = texto
        self.pos   = 0
        self.linha = 1

    def tokenizar(self):
        tokens = []
        while self.pos < len(self.texto):
            char = self.texto[self.pos]
            if char in ' \t\r': self.pos += 1; continue
            if char == '\n': self.linha += 1; self.pos += 1; continue
            if char == '#':
                while self.pos < len(self.texto) and self.texto[self.pos] != '\n': self.pos += 1
                continue

            # Operadores Simples
            if char == '{': tokens.append(Token(LBRACE, '{', self.linha)); self.pos += 1; continue
            if char == '}': tokens.append(Token(RBRACE, '}', self.linha)); self.pos += 1; continue
            if char == ':': tokens.append(Token(COLON, ':', self.linha)); self.pos += 1; continue
            if char == '%': tokens.append(Token(PERCENT, '%', self.linha)); self.pos += 1; continue
            if char == '+': tokens.append(Token(PLUS, '+', self.linha)); self.pos += 1; continue
            if char == '-': tokens.append(Token(MINUS, '-', self.linha)); self.pos += 1; continue
            if char == '*': tokens.append(Token(STAR, '*', self.linha)); self.pos += 1; continue
            if char == '/': tokens.append(Token(SLASH, '/', self.linha)); self.pos += 1; continue
            if char == '(': tokens.append(Token(LPAREN, '(', self.linha)); self.pos += 1; continue
            if char == ')': tokens.append(Token(RPAREN, ')', self.linha)); self.pos += 1; continue

            # Operadores Relacionais e Atribuição
            if char == '=':
                if self.pos + 1 < len(self.texto) and self.texto[self.pos+1] == '=':
                    tokens.append(Token(EQ, '==', self.linha)); self.pos += 2; continue
                tokens.append(Token(EQUAL, '=', self.linha)); self.pos += 1; continue
            if char == '>':
                if self.pos + 1 < len(self.texto) and self.texto[self.pos+1] == '=':
                    tokens.append(Token(GEQ, '>=', self.linha)); self.pos += 2; continue
                tokens.append(Token(GREATER, '>', self.linha)); self.pos += 1; continue
            if char == '<':
                if self.pos + 1 < len(self.texto) and self.texto[self.pos+1] == '=':
                    tokens.append(Token(LEQ, '<=', self.linha)); self.pos += 2; continue
                tokens.append(Token(LESS, '<', self.linha)); self.pos += 1; continue

            if char == '.' and self.pos + 1 < len(self.texto) and self.texto[self.pos + 1].isdigit():
                tokens.append(self._ler_decimal_implicito()); continue

            if char.isdigit(): tokens.append(self._ler_numero_ou_data()); continue
            if char.isalpha() or char == '_': tokens.append(self._ler_id_ou_keyword()); continue

            raise ErroLexico(f"Caractere inválido '{char}' na linha {self.linha}.")

        tokens.append(Token(EOF, None, self.linha))
        return tokens

    def _ler_decimal_implicito(self):
        linha = self.linha
        self.pos += 1
        inicio = self.pos
        while self.pos < len(self.texto) and self.texto[self.pos].isdigit(): self.pos += 1
        return Token(NUMBER, '0.' + self.texto[inicio:self.pos], linha)

    def _ler_numero_ou_data(self):
        inicio = self.pos
        linha  = self.linha
        while self.pos < len(self.texto) and self.texto[self.pos].isdigit(): self.pos += 1
        if self.pos < len(self.texto) and self.texto[self.pos] == '/': return self._ler_data(inicio, linha)
        if self.pos < len(self.texto) and self.texto[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.texto) and self.texto[self.pos].isdigit(): self.pos += 1
        return Token(NUMBER, self.texto[inicio:self.pos], linha)

    def _ler_data(self, inicio, linha):
        while self.pos < len(self.texto) and (self.texto[self.pos].isdigit() or self.texto[self.pos] == '/'): self.pos += 1
        valor = self.texto[inicio:self.pos]
        if not re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}', valor):
            raise ErroLexico(f"Formato de data inválido '{valor}' na linha {linha}.")
        return Token(DATE, valor, linha)

    def _ler_id_ou_keyword(self):
        inicio = self.pos
        linha  = self.linha
        while self.pos < len(self.texto) and (self.texto[self.pos].isalnum() or self.texto[self.pos] == '_'): self.pos += 1
        valor = self.texto[inicio:self.pos]
        return Token(KEYWORD if valor in KEYWORDS else ID, valor, linha)

class ErroLexico(Exception): pass