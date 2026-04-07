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
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"Erro Telegram: {e}")

def verificar_sinais():
    global ultimo_sinal
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando SOLUSDT...")

    try:
        resp = requests.get("https://api.binance.com/api/v3/klines", 
                           params={"symbol": "SOLUSDT", "interval": "1h", "limit": 100}, 
                           timeout=15)
        closes = [float(x[4]) for x in resp.json()]
        preco = closes[-1]

        sma5 = sum(closes[-5:]) / 5
        sma5_ant = sum(closes[-6:-1]) / 5
        sma21 = sum(closes[-21:]) / 21

        print(f"Preço: {preco:.2f} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}")

        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            msg = f"""🟢 <b>SINAL DE COMPRA - SOLUSDT</b>
💰 Preço: {preco:.2f}
📈 SMA5: {sma5:.2f}
📊 SMA21: {sma21:.2f}
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"

        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            msg = f"""🔴 <b>SINAL DE VENDA - SOLUSDT</b>
💰 Preço: {preco:.2f}
📈 SMA5: {sma5:.2f}
📊 SMA21: {sma21:.2f}
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"

    except Exception as e:
        print(f"Erro Binance: {e}")

# ==================== ROTAS ====================
@app.route('/')
def home():
    return """
    <h1>✅ Servidor de Sinais SOLUSDT</h1>
    <p><strong>Status:</strong> Rodando automaticamente</p>
    <p>Os sinais são enviados automaticamente a cada 60 segundos.</p>
    <p><a href='/teste'>🧪 Enviar Teste Telegram</a></p>
    """

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste Manual - Servidor funcionando normalmente!")
    return "✅ Teste enviado ao Telegram!"

if __name__ == '__main__':
    # Inicia a verificação automática em background
    thread = threading.Thread(target=lambda: [verificar_sinais() or time.sleep(60) for _ in iter(int, 1)], daemon=True)
    thread.start()
    
    print("🚀 Servidor iniciado - Verificação automática rodando!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
