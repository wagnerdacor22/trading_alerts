import os
import time
import threading
import requests
import pandas as pd
import numpy as np
from flask import Flask
from datetime import datetime

# Configuração do Flask
app = Flask(__name__)

# --- VARIÁVEIS DE AMBIENTE ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def enviar_telegram(msg):
    if TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        except:
            pass

def logica_do_bot():
    """ Função que executa a análise técnica """
    agora = datetime.now().strftime('%H:%M:%S')
    try:
        # Busca 100 velas de 1h
        url = "https://api.binance.com/api/v3/klines"
        res = requests.get(url, params={"symbol": "SOLUSDT", "interval": "1h", "limit": 100}, timeout=15)
        
        if res.status_code != 200:
            print(f"[{agora}] Erro na Binance: {res.status_code}", flush=True)
            return

        df = pd.DataFrame(res.json(), columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # Médias e Bandwidth
        df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()
        df['std'] = df['close'].rolling(window=21).std()
        df['bw'] = (( (df['sma21'] + 2*df['std']) - (df['sma21'] - 2*df['std']) ) / df['sma21']) * 100

        # Valores atuais
        c = df['close'].iloc[-1]
        e5 = df['ema5'].iloc[-1]
        s21 = df['sma21'].iloc[-1]
        bw = df['bw'].iloc[-1]

        filtro = 1.535
        status = "✅ OK" if bw > filtro else "💤 LATERAL"
        
        # LOG CRITICAL: Isso PRECISA aparecer no Railway
        print(f"[{agora}] SOL: ${c:.2f} | BW: {bw:.3f}% | {status}", flush=True)

        # Lógica de cruzamento simplificada para teste
        global ultimo_sinal
        if bw > filtro:
            if e5 > s21 and globals().get('ultimo_sinal') != "COMPRA":
                enviar_telegram(f"🟢 SOL COMPRA (1H)\nPreço: {c}\nBW: {bw:.3f}%")
                globals()['ultimo_sinal'] = "COMPRA"
            elif e5 < s21 and globals().get('ultimo_sinal') != "VENDA":
                enviar_telegram(f"🔴 SOL VENDA (1H)\nPreço: {c}\nBW: {bw:.3f}%")
                globals()['ultimo_sinal'] = "VENDA"

    except Exception as e:
        print(f"❌ ERRO: {str(e)}", flush=True)

def monitor():
    print("🚀 INICIANDO MONITORAMENTO...", flush=True)
    while True:
        logica_do_bot()
        time.sleep(60)

# Inicia o monitor em segundo plano
threading.Thread(target=monitor, daemon=True).start()

@app.route('/')
def index():
    return "BOT RODANDO"

if __name__ == '__main__':
    # Railway usa a variável PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
