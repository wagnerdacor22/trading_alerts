from flask import Flask
import requests
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
# Pegas das variáveis de ambiente do Railway
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
ultimo_sinal = None

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Variáveis do Telegram não configuradas!")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def logica_do_bot():
    global ultimo_sinal
    agora = datetime.now().strftime('%H:%M:%S')
    
    try:
        # Tenta conectar na Binance
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 30}
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code != 200:
            return f"[{agora}] Erro Binance: Status {resp.status_code}"

        dados = resp.json()
        closes = [float(x[4]) for x in dados]
        preco = closes[-1]

        # Cálculos de Média Móvel
        sma5 = sum(closes[-5:]) / 5
        sma21 = sum(closes[-21:]) / 21
        sma5_ant = sum(closes[-6:-1]) / 5

        status = f"Preço: ${preco:.2f} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}"
        print(f"[{agora}] {status}")

        # Lógica de Cruzamento
        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            msg = f"🟢 <b>COMPRA SOLUSDT</b>\n💰 Preço: {preco:.2f}\n📊 SMA5 cruzou SMA21 para cima!"
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"
        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            msg = f"🔴 <b>VENDA SOLUSDT</b>\n💰 Preço: {preco:.2f}\n📊 SMA5 cruzou SMA21 para baixo!"
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"
            
        return status

    except Exception as e:
        print(f"❌ Erro na lógica: {e}")
        return f"Erro: {str(e)}"

# --- THREAD DE MONITORAMENTO (Roda sempre que o servidor ligar) ---
def monitor_loop():
    print("🤖 Iniciando monitoramento automático...")
    while True:
        logica_do_bot()
        time.sleep(60) # Verifica a cada 1 minuto

# Inicia a thread globalmente (importante para o Gunicorn)
t = threading.Thread(target=monitor_loop, daemon=True)
t.start()

# --- ROTAS FLASK ---

@app.route('/')
def home():
    return """
    <h1>✅ Bot SOLUSDT Online</h1>
    <p>O monitoramento automático está rodando a cada 60s.</p>
    <ul>
        <li><a href='/verificar'>🔄 Forçar Verificação Agora</a></li>
        <li><a href='/teste'>🧪 Testar Telegram</a></li>
    </ul>
    """

@app.route('/verificar')
def verificar():
    # Esta rota executa a mesma lógica da thread, mas mostra o resultado na tela
    resultado = logica_do_bot()
    return f"<h2>Resultado da Análise:</h2><p>{resultado}</p><br><a href='/'>Voltar</a>"

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste de Conexão: O Bot está funcionando!")
    return "✅ Sinal de teste enviado ao Telegram!<br><a href='/'>Voltar</a>"

if __name__ == '__main__':
    # Usado apenas para rodar localmente (o Railway usa o Procfile)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
