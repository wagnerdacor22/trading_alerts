from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

# Configurações de Ambiente
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
ultimo_sinal = None

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def logica_do_bot():
    global ultimo_sinal
    try:
        # Pega os dados da Binance (1h candle)
        resp = requests.get("https://api.binance.com/api/v3/klines", 
                           params={"symbol": "SOLUSDT", "interval": "1h", "limit": 30}, timeout=10)
        dados = resp.json()
        closes = [float(x[4]) for x in dados]
        preco = closes[-1]

        sma5 = sum(closes[-5:]) / 5
        sma21 = sum(closes[-21:]) / 21
        sma5_ant = sum(closes[-6:-1]) / 5

        status = f"Preço: {preco:.2f} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status}")

        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            enviar_telegram(f"🟢 <b>COMPRA SOLUSDT</b>\nPreço: {preco}")
            ultimo_sinal = "COMPRA"
        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            enviar_telegram(f"🔴 <b>VENDA SOLUSDT</b>\nPreço: {preco}")
            ultimo_sinal = "VENDA"
            
        return status
    except Exception as e:
        return f"Erro: {e}"

# --- ESTA PARTE É A CHAVE ---
# Definimos o loop e iniciamos a thread FORA do __main__
def background_loop():
    while True:
        logica_do_bot()
        time.sleep(60)

# Inicia assim que o Gunicorn importar o arquivo
t = threading.Thread(target=background_loop, daemon=True)
t.start()
# ----------------------------

@app.route('/')
def home():
    return "<h1>Bot SOLUSDT Rodando</h1>"

@app.route('/verificar')
def verificar():
    res = logica_do_bot()
    return f"Verificação manual: {res}"

# O bloco abaixo só roda se você der 'python main.py' localmente
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
