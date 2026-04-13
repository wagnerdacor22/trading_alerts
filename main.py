import os
import time
import threading
import requests
import pandas as pd
import pandas_ta as ta
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
        # 1. Busca dados de 1 hora
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 100} 
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return f"Erro Binance: {resp.status_code}"

        dados = resp.json()
        df = pd.DataFrame(dados, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # 2. Cálculos das Médias Simples (SMA)
        df['sma5'] = df['close'].rolling(window=5).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()

        # 3. Cálculo do MACD (6, 15, 1)
        # fast=6, slow=15, signal=1
        macd = ta.macd(df['close'], fast=6, slow=15, signal=1)
        # O pandas_ta gera nomes específicos para as colunas:
        df['macd'] = macd['MACD_6_15_1']
        df['macd_sinal'] = macd['MACDs_6_15_1']

        # Valores Atuais
        atual_sma5 = df['sma5'].iloc[-1]
        atual_sma21 = df['sma21'].iloc[-1]
        atual_macd = df['macd'].iloc[-1]
        atual_macd_sinal = df['macd_sinal'].iloc[-1]
        
        preco_atual = df['close'].iloc[-1]

        status = f"Preço: ${preco_atual:.2f} | SMA5: {atual_sma5:.2f} | SMA21: {atual_sma21:.2f} | MACD: {atual_macd:.2f}"
        print(f"[{agora}] {status}", flush=True)

        # 4. Lógica de Cruzamento Duplo (Médias + MACD)
        
        # CONDIÇÃO DE COMPRA:
        # SMA5 acima da SMA21 E MACD acima da linha de sinal (ou acima de zero)
        if atual_sma5 > atual_sma21 and atual_macd > atual_macd_sinal:
            if ultimo_sinal != "COMPRA":
                msg = f"🟢 <b>SOL/USDT (1H): COMPRA CONFIRMADA</b>\n💰 Preço: {preco_atual:.2f}\n📊 SMA5 > SMA21\n📈 MACD (6,15,1) em Alta!"
                enviar_telegram(msg)
                ultimo_sinal = "COMPRA"
        
        # CONDIÇÃO DE VENDA:
        # SMA5 abaixo da SMA21 E MACD abaixo da linha de sinal
        elif atual_sma5 < atual_sma21 and atual_macd < atual_macd_sinal:
            if ultimo_sinal != "VENDA":
                msg = f"🔴 <b>SOL/USDT (1H): VENDA CONFIRMADA</b>\n💰 Preço: {preco_atual:.2f}\n📊 SMA5 < SMA21\n📉 MACD (6,15,1) em Baixa!"
                enviar_telegram(msg)
                ultimo_sinal = "VENDA"
            
        return status

    except Exception as e:
        print(f"❌ Erro na lógica: {e}")
        return f"Erro: {str(e)}"

# --- MONITORAMENTO ---
def monitor_loop():
    print("🤖 Bot iniciado: Cruzamento SMA + MACD (6,15,1)")
    while True:
        logica_do_bot()
        time.sleep(60) 

threading.Thread(target=monitor_loop, daemon=True).start()

# --- ROTAS FLASK ---
@app.route('/')
def home():
    return f"Bot Ativo (Filtro MACD 6,15,1). Último sinal: {ultimo_sinal}"

@app.route('/verificar')
def verificar():
    resultado = logica_do_bot()
    return f"<h2>Status Atual:</h2><p>{resultado}</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
