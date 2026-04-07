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
ultima_verificacao = None

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TOKEN ou CHAT_ID não configurados!")
        return None
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Erro Telegram: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")
        return None

def calcular_sma(closes, period):
    return sum(closes[-period:]) / period

def verificar_sinais():
    global ultimo_sinal, ultima_verificacao
    
    print(f"[{datetime.now()}] Verificando sinais...")  # Log importante
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",
        "limit": 100  # Aumentado para maior segurança
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        closes = [float(candle[4]) for candle in data]
        preco_atual = closes[-1]
        
        # Cálculo correto
        sma5_atual = calcular_sma(closes, 5)
        sma5_anterior = calcular_sma(closes[:-1], 5)  # Mais correto
        sma21 = calcular_sma(closes, 21)
        
        print(f"Preço: {preco_atual:.2f} | SMA5: {sma5_atual:.2f} | SMA21: {sma21:.2f}")

        sinal = None
        
        # Crossover de alta (Compra)
        if sma5_anterior < sma21 and sma5_atual >= sma21:
            if ultimo_sinal != "COMPRA":
                sinal = "COMPRA"
                mensagem = f"""🟢 <b>SINAL DE COMPRA - SOLUSDT</b>
💰 Preço: <code>{preco_atual:.2f}</code>
📈 SMA 5: <code>{sma5_atual:.2f}</code>
📊 SMA 21: <code>{sma21:.2f}</code>
⏰ Timeframe: 1H
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
                enviar_telegram(mensagem)
                ultimo_sinal = "COMPRA"
        
        # Crossover de baixa (Venda)
        elif sma5_anterior > sma21 and sma5_atual <= sma21:
            if ultimo_sinal != "VENDA":
                sinal = "VENDA"
                mensagem = f"""🔴 <b>SINAL DE VENDA - SOLUSDT</b>
💰 Preço: <code>{preco_atual:.2f}</code>
📈 SMA 5: <code>{sma5_atual:.2f}</code>
📊 SMA 21: <code>{sma21:.2f}</code>
⏰ Timeframe: 1H
🕒 {datetime.now().strftime('%d/%m %H:%M')}"""
                enviar_telegram(mensagem)
                ultimo_sinal = "VENDA"
        
        ultima_verificacao = datetime.now()
        return sinal or "Nenhum sinal"
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return f"Erro: {e}"

def loop_verificacao():
    print("🔄 Thread de verificação iniciada...")
    while True:
        verificar_sinais()
        time.sleep(60)  # Verifica a cada 60 segundos

@app.route('/')
def home():
    return """
    ✅ <h1>Servidor de Sinais SOLUSDT rodando!</h1>
    <p>Último sinal: {}</p>
    <p><a href='/verificar'>Verificar agora</a></p>
    """.format(ultimo_sinal or "Nenhum ainda")

@app.route('/teste')
def teste():
    enviar_telegram("🧪 <b>Teste de conexão!</b>\nServidor funcionando normalmente ✅")
    return "Teste enviado ao Telegram!"

@app.route('/verificar')
def verificar():
    resultado = verificar_sinais()
    return f"✅ Verificação manual executada: {resultado}<br>Último sinal: {ultimo_sinal}"

if __name__ == '__main__':
    thread = threading.Thread(target=loop_verificacao, daemon=True)
    thread.start()
    
    print("🚀 Servidor iniciado com logs aprimorados!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
