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
        print("❌ TOKEN ou CHAT_ID não configurados!")
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram enviado com sucesso")
        else:
            print(f"❌ Telegram falhou: {r.text}")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def calcular_sma(closes, period):
    return sum(closes[-period:]) / period if len(closes) >= period else sum(closes) / len(closes)

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
        
        sma5 = calcular_sma(closes, 5)
        sma5_ant = calcular_sma(closes[:-1], 5)
        sma21 = calcular_sma(closes, 21)

        print(f"Preço: {preco:.2f} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}")

        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            msg = f"""🟢 <b>SINAL DE COMPRA - SOLUSDT</b>
💰 Preço: <code>{preco:.2f}</code>
📈 SMA5: <code>{sma5:.2f}</code>
📊 SMA21: <code>{sma21:.2f}</code>
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"

        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            msg = f"""🔴 <b>SINAL DE VENDA - SOLUSDT</b>
💰 Preço: <code>{preco:.2f}</code>
📈 SMA5: <code>{sma5:.2f}</code>
📊 SMA21: <code>{sma21:.2f}</code>
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"

    except Exception as e:
        print(f"❌ Erro: {e}")

def loop_verificacao():
    while True:
        verificar_sinais()
        time.sleep(60)

@app.route('/')
def home():
    return "✅ <h1>Servidor SOLUSDT rodando no Railway!</h1>"

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste do Railway - Servidor OK!")
    return "Teste enviado!"

@app.route('/verificar')
def verificar():
    verificar_sinais()
    return "Verificação manual feita!"

if __name__ == '__main__':
    thread = threading.Thread(target=loop_verificacao, daemon=True)
    thread.start()
    print("🚀 Servidor iniciado!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
