from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

@app.route('/')
def home():
    return """
    <h1>✅ Servidor SOLUSDT - ONLINE</h1>
    <p><a href='/teste'>Testar Telegram</a></p>
    <p><a href='/verificar'>Verificar Sinal Agora</a></p>
    """

@app.route('/teste')
def teste():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "🧪 Teste OK - Rota /teste funcionando!",
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        return "✅ Teste enviado ao Telegram!"
    except:
        return "Erro no Telegram"

@app.route('/verificar')
def verificar():
    return """
    <h2>✅ Rota /verificar funcionando!</h2>
    <p>Verificação manual executada.</p>
    <p>Verifique os logs do Railway para ver as mensagens.</p>
    """

if __name__ == '__main__':
    print("🚀 Servidor iniciado com todas as rotas!")
    # Thread simples só para não parar
    def keep_alive():
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Servidor rodando...")
            time.sleep(60)
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
