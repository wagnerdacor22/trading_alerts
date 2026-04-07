from flask import Flask, request, jsonify
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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Erro: {e}")
        return None

def verificar_sinais():
    global ultimo_sinal
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",
        "limit": 50
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        closes = [float(candle[4]) for candle in data]
        
        ema5 = sum(closes[-5:]) / 5
        ema5_anterior = sum(closes[-6:-1]) / 5
        
        sma21 = sum(closes[-21:]) / 21
        
        preco_atual = closes[-1]
        
        if ema5_anterior < sma21 and ema5 >= sma21:
            if ultimo_sinal != "COMPRA":
                mensagem = f"""🟢 <b>SINAL DE COMPRA SOLUSDT</b>

💰 Preço: {preco_atual:.2f}
📈 EMA 5: {ema5:.2f}
📊 BB Central: {sma21:.2f}
⏰ Timeframe: 1H"""
                enviar_telegram(mensagem)
                ultimo_sinal = "COMPRA"
                print(f"Compra enviada: {preco_atual}")
                return "COMPRA"
        
        elif ema5_anterior > sma21 and ema5 <= sma21:
            if ultimo_sinal != "VENDA":
                mensagem = f"""🔴 <b>SINAL DE VENDA SOLUSDT</b>

💰 Preço: {preco_atual:.2f}
📈 EMA 5: {ema5:.2f}
📊 BB Central: {sma21:.2f}
⏰ Timeframe: 1H"""
                enviar_telegram(mensagem)
                ultimo_sinal = "VENDA"
                print(f"Venda enviada: {preco_atual}")
                return "VENDA"
        
        return "Nenhum sinal"
        
    except Exception as e:
        print(f"Erro: {e}")
        return f"Erro: {e}"

def loop_verificacao():
    while True:
        verificar_sinais()
        time.sleep(60)

@app.route('/')
def home():
    return "✅ Servidor de Sinais SOLUSDT rodando!"

@app.route('/teste')
def teste():
    mensagem = "🧪 <b>Teste de conexão!</b>\n\nServidor está funcionando! ✅"
    enviar_telegram(mensagem)
    return "Teste enviado!"

@app.route('/verificar')
def verificar():
    resultado = verificar_sinais()
    return f"Verificação executada: {resultado}"

if __name__ == '__main__':
    thread = threading.Thread(target=loop_verificacao)
    thread.daemon = True
    thread.start()
    
    print("🚀 Servidor iniciado!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
