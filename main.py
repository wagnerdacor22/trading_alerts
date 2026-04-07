from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

ultimo_sinal = None

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TOKEN ou CHAT_ID não configurado")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        r = requests.post(url, json=payload, timeout=10)
        print(f"Telegram: {r.status_code}")
    except Exception as e:
        print(f"Erro Telegram: {e}")

def verificar_sinais():
    global ultimo_sinal
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando SOLUSDT...")

    try:
        resp = requests.get("https://api.binance.com/api/v3/klines",
            params={"symbol": "SOLUSDT", "interval": "1h", "limit": 100},
            timeout=15)
        resp.raise_for_status()
        closes = [float(x[4]) for x in resp.json()]
        preco = closes[-1]

        sma5 = sum(closes[-5:]) / 5
        sma5_ant = sum(closes[-6:-1]) / 5 if len(closes) > 5 else sma5
        sma21 = sum(closes[-21:]) / 21

        print(f"Preço: {preco:.2f} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}")

        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            msg = f"🟢 <b>SINAL DE COMPRA - SOLUSDT</b>\nPreço: {preco:.2f}"
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"
            return "✅ SINAL DE COMPRA ENVIADO"

        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            msg = f"🔴 <b>SINAL DE VENDA - SOLUSDT</b>\nPreço: {preco:.2f}"
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"
            return "✅ SINAL DE VENDA ENVIADO"

        return "Nenhum sinal novo"

    except Exception as e:
        print(f"Erro: {e}")
        return "Erro na API"

def loop_verificacao():
    while True:
        verificar_sinais()
        time.sleep(60)

@app.route('/')
def home():
    return "✅ Servidor SOLUSDT Online!"

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste OK - Servidor funcionando!")
    return "Teste enviado!"

@app.route('/verificar')
def verificar():
    resultado = verificar_sinais()
    return f"<h2>Verificação Manual</h2><p>Resultado: <strong>{resultado}</strong></p>"

if __name__ == '__main__':
    thread = threading.Thread(target=loop_verificacao, daemon=True)
    thread.start()
    print("🚀 Servidor iniciado!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
