import os
import time
import threading
import requests
import pandas as pd
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
        # 1. Busca os dados de 1 hora (1h)
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 100} 
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return f"Erro Binance: {resp.status_code}"

        dados = resp.json()
        df = pd.DataFrame(dados, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # 2. Cálculos das Médias Móveis (SMA)
        # O cálculo usa as velas de 1h, mas o último valor (índice -1) 
        # atualiza em tempo real conforme o preço mexe agora.
        df['sma5'] = df['close'].rolling(window=5).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()

        atual_sma5 = df['sma5'].iloc[-1]
        atual_sma21 = df['sma21'].iloc[-1]
        preco_atual = df['close'].iloc[-1]

        status = f"Preço: ${preco_atual:.2f} | SMA5: {atual_sma5:.2f} | SMA21: {atual_sma21:.2f}"
        print(f"[{agora}] {status}", flush=True)

        # 3. Lógica de Cruzamento "No Momento"
        # Se SMA5 ficar maior que SMA21 agora, envia COMPRA
        if atual_sma5 > atual_sma21 and ultimo_sinal != "COMPRA":
            msg = f"🟢 <b>SOL/USDT (1H): COMPRA INSTANTÂNEA</b>\n💰 Preço: {preco_atual:.2f}\n📈 SMA5 ultrapassou a SMA21 agora!"
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"
        
        # Se SMA5 ficar menor que SMA21 agora, envia VENDA
        elif atual_sma5 < atual_sma21 and ultimo_sinal != "VENDA":
            msg = f"🔴 <b>SOL/USDT (1H): VENDA INSTANTÂNEA</b>\n💰 Preço: {preco_atual:.2f}\n📉 SMA5 caiu abaixo da SMA21 agora!"
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"
            
        return status

    except Exception as e:
        print(f"❌ Erro: {e}")
        return f"Erro: {str(e)}"

# --- MONITORAMENTO ---
def monitor_loop():
    # O bot checa a cada 60 segundos, independente da vela de 1h ter fechado ou não
    print("🤖 Monitoramento Instantâneo 1H (SMA5 vs SMA21) Iniciado")
    while True:
        logica_do_bot()
        time.sleep(60) 

threading.Thread(target=monitor_loop, daemon=True).start()

# --- ROTAS ---
@app.route('/')
def home():
    return f"Bot SMA 1H Ativo. Status: {ultimo_sinal if ultimo_sinal else 'Aguardando Cruzamento'}"

@app.route('/verificar')
def verificar():
    resultado = logica_do_bot()
    return f"<h2>Análise Atual (1h):</h2><p>{resultado}</p>"

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste: O bot está te ouvindo e monitorando o gráfico de 1H!")
    return "✅ Teste enviado!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
