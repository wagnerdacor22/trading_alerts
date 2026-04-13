import os
import time
import threading
import requests
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
ultimo_sinal = None

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro Telegram: {e}", flush=True)

def logica_do_bot():
    global ultimo_sinal
    agora = datetime.now().strftime('%H:%M:%S')
    
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 100} 
        resp = requests.get(url, params=params, timeout=15)
        
        if resp.status_code != 200:
            print(f"[{agora}] Erro Binance: {resp.status_code}", flush=True)
            return
            
        dados = resp.json()
        df = pd.DataFrame(dados, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # Cálculos
        df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()
        df['stddev'] = df['close'].rolling(window=21).std()
        df['upper'] = df['sma21'] + (2 * df['stddev'])
        df['lower'] = df['sma21'] - (2 * df['stddev'])
        df['bandwidth'] = ((df['upper'] - df['lower']) / df['sma21']) * 100

        if df['bandwidth'].isnull().iloc[-1]:
            print(f"[{agora}] Aguardando dados...", flush=True)
            return

        atual_ema5 = df['ema5'].iloc[-1]
        atual_sma21 = df['sma21'].iloc[-1]
        bw_atual = df['bandwidth'].iloc[-1]
        preco_atual = df['close'].iloc[-1]

        filtro_lateral = 1.535
        mercado_vivo = bw_atual > filtro_lateral

        # O segredo está aqui: o flush=True força o Railway a mostrar a linha NA HORA
        status = f"SOL: ${preco_atual:.2f} | BW: {bw_atual:.3f}% | {'✅ OK' if mercado_vivo else '💤 LATERAL'}"
        print(f"[{agora}] {status}", flush=True)

        if mercado_vivo:
            if atual_ema5 > atual_sma21 and ultimo_sinal != "COMPRA":
                msg = f"🟢 <b>SOL COMPRA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}%"
                enviar_telegram(msg)
                ultimo_sinal = "COMPRA"
            
            elif atual_ema5 < atual_sma21 and ultimo_sinal != "VENDA":
                msg = f"🔴 <b>SOL VENDA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}%"
                enviar_telegram(msg)
                ultimo_sinal = "VENDA"
            
    except Exception as e:
        print(f"❌ Erro: {e}", flush=True)

# --- MONITORAMENTO ---
def monitor_loop():
    # Mensagem de início imediata
    print("🤖 Bot iniciado! Monitorando a cada 60s...", flush=True)
    while True:
        logica_do_bot()
        time.sleep(60) 

# Inicia a thread
monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
monitor_thread.start()

# --- ROTAS ---
@app.route('/')
def home():
    return f"Bot SOL 1H Ativo. Filtro: 1.535%. Status: {ultimo_sinal}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Threaded=True ajuda o Flask a não travar o loop do bot
    app.run(host='0.0.0.0', port=port, threaded=True)
