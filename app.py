import io
import contextlib

from flask import Flask, request, jsonify
from flask_cors import CORS

from lexer         import Lexer, ErroLexico
from parser        import Parser, ErroSintatico
from semantico     import AnalisadorSemantico, ErroSemantico
from interpretador import Interpretador

app = Flask(__name__)
CORS(app)

def _compilar_e_executar(codigo_fonte: str):
    try:
        tokens = Lexer(codigo_fonte).tokenizar()
    except ErroLexico as e:
        return False, '', 'lexico', str(e), None

    try:
        arvore = Parser(tokens).parsear()
    except ErroSintatico as e:
        return False, '', 'sintatico', str(e), None

    try:
        semantico = AnalisadorSemantico()
        semantico.analisar(arvore)
    except ErroSemantico as e:
        return False, '', 'semantico', str(e), None

    buffer = io.StringIO()
    graficos = None
    try:
        with contextlib.redirect_stdout(buffer):
            if semantico.alertas:
                print("--- Alertas Semânticos ---")
                for alerta in semantico.alertas: print(f"  {alerta}")
                print()

            interprete = Interpretador(semantico.tabela)
            interprete.executar(arvore)
            graficos = interprete.dados_grafico # Extração dos dados pro Chart.js
    except Exception as e:
        return False, '', 'interno', f"Erro em tempo de execução: {e}", None

    return True, buffer.getvalue(), '', '', graficos

@app.route('/compilar', methods=['POST'])
def compilar():
    dados = request.get_json(silent=True)
    if not dados or 'codigo' not in dados:
        return jsonify({'ok': False, 'erro': "JSON inválido.", 'tipo': 'interno'}), 400

    ok, saida, tipo_erro, msg_erro, graficos = _compilar_e_executar(dados['codigo'])

    if ok:
        return jsonify({'ok': True, 'saida': saida, 'graficos': graficos})
    else:
        return jsonify({'ok': False, 'erro': msg_erro, 'tipo': tipo_erro}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)