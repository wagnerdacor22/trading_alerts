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
        print(f"❌ Erro Telegram: {e}")

def logica_do_bot():
    global ultimo_sinal
    agora = datetime.now().strftime('%H:%M:%S')
    
    try:
        # 1. Busca dados de 1 hora (pedimos 100 velas para ter histórico pro cálculo)
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 100} 
        resp = requests.get(url, params=params, timeout=15)
        
        if resp.status_code != 200:
            return f"Erro Binance: {resp.status_code}"

        dados = resp.json()
        df = pd.DataFrame(dados, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # 2. Cálculos Técnicos
        # EMA 5 e SMA 21
        df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()
        
        # Bandwidth (Largura das Bandas) para o seu filtro de 1.535%
        df['stddev'] = df['close'].rolling(window=21).std()
        df['upper'] = df['sma21'] + (2 * df['stddev'])
        df['lower'] = df['sma21'] - (2 * df['stddev'])
        df['bandwidth'] = ((df['upper'] - df['lower']) / df['sma21']) * 100

        # Verificação de segurança: Se os cálculos ainda forem NaN (vazios), aborta
        if df['bandwidth'].isnull().iloc[-1]:
            return "Aguardando histórico de dados..."

        atual_ema5 = df['ema5'].iloc[-1]
        atual_sma21 = df['sma21'].iloc[-1]
        bw_atual = df['bandwidth'].iloc[-1]
        preco_atual = df['close'].iloc[-1]

        # SEU FILTRO PERSONALIZADO
        filtro_lateral = 1.535
        mercado_vivo = bw_atual > filtro_lateral

        status = f"Preço: {preco_atual:.2f} | BW: {bw_atual:.3f}% | {'✅ OK' if mercado_vivo else '💤 LATERAL'}"
        print(f"[{agora}] {status}", flush=True)

        # 3. Gatilho de Sinal
        if mercado_vivo:
            # Cruzamento de Compra
            if atual_ema5 > atual_sma21 and ultimo_sinal != "COMPRA":
                msg = f"🟢 <b>SOL COMPRA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}%"
                enviar_telegram(msg)
                ultimo_sinal = "COMPRA"
            
            # Cruzamento de Venda
            elif atual_ema5 < atual_sma21 and ultimo_sinal != "VENDA":
                msg = f"🔴 <b>SOL VENDA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}%"
                enviar_telegram(msg)
                ultimo_sinal = "VENDA"
            
        return status

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        return f"Erro: {str(e)}"

# --- MONITORAMENTO ---
def monitor_loop():
    print("🤖 Bot Iniciado com Filtro de Lateralidade (1.535%)")
    while True:
        logica_do_bot()
        time.sleep(45) # Checa a cada 45 segundos

threading.Thread(target=monitor_loop, daemon=True).start()

# --- ROTAS ---
@app.route('/')
def home():
    return f"Bot Online. Filtro: 1.535%. Status atual: {ultimo_sinal if ultimo_sinal else 'Monitorando...'}"

@app.route('/verificar')
def verificar():
    resultado = logica_do_bot()
    return f"<h2>Análise em Tempo Real:</h2><p>{resultado}</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
