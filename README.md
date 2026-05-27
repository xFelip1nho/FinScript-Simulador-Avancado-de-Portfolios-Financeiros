# FinScript — Simulador de Portfólios Financeiros (DSL)

O FinScript é uma Linguagem de Domínio Específico (DSL) desenvolvida como
projeto prático para a disciplina de Teoria da Computação e Compiladores.
A linguagem permite declarar ativos financeiros, compor portfólios, simular
rendimentos com aportes mensais e gerar relatórios gráficos de rentabilidade
líquida, alinhada com a realidade do mercado financeiro brasileiro.

Autores: Felipe Pinheiro, João Pedro Rebelato, Julio Cezar Da Cunha
Instituição: Fundação Hermínio Ometto (FHO) — Araras, SP, Brasil

---

## Funcionalidades Principais

1. Motor Visual e Gráficos Dinâmicos
   - Gráfico de Linha (Simular): Plota a evolução do patrimônio bruto e
     líquido mês a mês durante o período simulado.
   - Gráfico de Pizza (Comparar): Exibe a distribuição percentual do
     patrimônio final entre dois portfólios concorrentes.
   - Interface Dark Mode: Painel web responsivo com modo escuro.

2. Realismo Financeiro
   - Aportes Mensais Periódicos: Simulação de depósitos recorrentes mensais
     via fórmula de Valor Futuro de Anuidade com juros compostos.
   - Tabela Regressiva de IR: Dedução automática sobre o lucro de ativos
     de renda_fixa conforme o prazo de resgate:
       * Até 6 meses:    22,5%
       * 7 a 12 meses:   20,0%
       * 13 a 24 meses:  17,5%
       * Acima de 24:    15,0%
   - Indexadores do mercado brasileiro: CDI (10,65% a.a.), SELIC (10,75% a.a.),
     IPCA (4,83% a.a.) e taxa prefixada.

3. Estruturas Condicionais e Variáveis na DSL
   - Blocos condicionais (se / entao / fim) avaliados durante a análise
     semântica, antes da execução.
   - Variáveis globais com expressões aritméticas via comando definir.
   - Operadores relacionais suportados: ==, >, <, >=, <=.

4. Exportação e Importação de Dados
   - Botão Exportar: Salva todos os ativos e portfólios cadastrados em um
     arquivo JSON (finscript_dados.json) na máquina do usuário.
   - Botão Importar: Carrega um arquivo JSON exportado anteriormente,
     restaurando todos os ativos e portfólios na interface sem precisar
     recadastrá-los.
   - Fluxo recomendado: cadastrar os dados → exportar o JSON → enviar o JSON
     junto com o projeto → o destinatário importa e testa normalmente.

---

## Arquitetura do Sistema

O projeto adota uma arquitetura cliente-servidor de duas camadas:

  [Interface HTML / Frontend] <-- HTTP JSON --> [Flask API / Backend Python]

- Frontend (interface.html): SPA que gera o código-fonte FinScript a partir
  dos dados cadastrados e o envia ao backend via fetch assíncrono.
- Backend (app.py): Servidor Flask que executa as 4 fases do compilador e
  devolve a saída textual e os dados de gráficos em JSON.

---

## Estrutura de Arquivos

- lexer.py       — Analisador Léxico: converte o código-fonte em tokens tipados,
                   trata datas, comentários (#) e operadores compostos (>=, <=, ==).
- parser.py      — Analisador Sintático: parser descendente recursivo que constrói
                   a AST respeitando precedência de operadores.
- ast_nos.py     — Nós da Árvore Sintática Abstrata (AST): hierarquia de objetos
                   para cada construtor da linguagem.
- semantico.py   — Analisador Semântico: tabela de símbolos, verificação de tipos,
                   campos obrigatórios por tipo de ativo e regras de negócio.
- interpretador.py — Motor de Execução: caminha a AST, aplica juros compostos,
                   deduz IR regressivo e gera os dados para os gráficos.
- app.py         — Backend Flask: expõe o endpoint POST /compilar e coordena
                   as fases do compilador.
- interface.html — Frontend: formulários de cadastro, botões Exportar/Importar,
                   painel de resultados e gráficos via Chart.js.

---

## Gramática FinScript

### Declaração de Ativo

  ativo <nome> {
      tipo          : renda_fixa | acao | fundo
      quantidade    : <inteiro positivo>
      preco_medio   : <decimal>
      aporte_mensal : <decimal>                      # Opcional (padrão: 0)
      taxa          : <decimal> %                    # Obrigatório: renda_fixa e fundo
      indexador     : CDI | SELIC | IPCA | prefixado # Exclusivo: renda_fixa
      vencimento    : dd/mm/aaaa                     # Obrigatório: renda_fixa
  }

### Declaração de Portfólio

  portfolio <nome> {
      ativo : <nome_do_ativo>
      ativo : <nome_do_ativo>
      ...
  }

### Variáveis e Condicionais

  definir <variavel> = <expressao_aritmetica>

  se <variavel> <operador> <valor> entao
      <comandos>
  fim

### Comandos de Execução

  simular  <portfolio> periodo : <n> meses
  relatorio <portfolio> rentabilidade
  comparar  <portfolio_a> com <portfolio_b>

---

## Instalação e Execução

Requisitos: Python 3.8 ou superior.

1. Instalar dependências:
   pip install flask flask-cors

2. Iniciar o backend:
   python app.py
   O servidor ficará disponível em http://localhost:5000.

3. Abrir o frontend:
   Abra o arquivo interface.html em qualquer navegador moderno.
   O backend precisa estar rodando para as simulações funcionarem.
4. Importe o Ativos-Portifolio com os ativos/portifolios que foram préviamente cadastrados, apenas para testar.
---

## Validações Semânticas

O compilador detecta e reporta os seguintes erros e alertas:

Erros (interrompem a execução):
- Indexador incompatível: CDI/SELIC/IPCA aplicados a acao ou fundo.
- Campo obrigatório ausente: renda_fixa sem taxa, indexador ou vencimento.
- Símbolo não declarado: simular/relatorio/comparar com nome inexistente.
- Categoria errada: simular aplicado a um ativo (não a um portfólio).
- Quantidade não-inteira: ex. quantidade: 10.5 — exibe o valor inválido.
- Divisão por zero: em expressões aritméticas do comando definir.

Alertas (executam com aviso):
- Concentração de risco: ativo representa mais de 80% do valor do portfólio.
- Vencimento passado: data de vencimento anterior à data atual da simulação.

---

## Convenção de Taxa para Ativos do Tipo Fundo

- taxa > 30 → interpretada como % do CDI (ex: 110 = 110% do CDI ≈ 11,72% a.a.)
- taxa ≤ 30 → interpretada como taxa anual direta em % a.a. (ex: 9.5 = 9,5% a.a.)

Essa distinção reflete o mercado brasileiro: fundos DI são cotados como % do CDI,
enquanto fundos de gestão ativa declaram taxa fixa anual.

---

## Comportamento do Bloco Condicional SE

O bloco SE é avaliado durante a análise semântica. Se a condição for falsa,
os comandos internos não são analisados nem executados — ativos e portfólios
declarados dentro do bloco falso não são registrados na tabela de símbolos.
Variáveis (definir) podem ser redeclaradas, permitindo que dois blocos SE
mutuamente exclusivos atribuam valores diferentes à mesma variável.

---

Trabalho desenvolvido para a disciplina de Teoria da Computação e Compiladores
Fundação Hermínio Ometto (FHO) — Araras, SP, Brasil.
