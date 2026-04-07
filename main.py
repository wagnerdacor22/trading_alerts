from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Servidor Online - Versão Diagnóstico"

@app.route('/teste')
def teste():
    return "✅ Rota /teste funcionando!"

@app.route('/verificar')
def verificar():
    return "✅ Rota /verificar funcionando! (ainda sem sinais)"

print("🚀 App carregado com rotas simples")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
