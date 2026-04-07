from flask import Flask
import requests
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

# Configurações (Garanta que as variáveis de ambiente estejam no painel do Railway!)
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

def logica_do_bot():
    """Esta função contém a inteligência de cálculo do SOLUSDT"""
    global ultimo_sinal
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Analisando Binance...")
    
    try:
        resp = requests.get("https://api.binance.com/api/v3/klines", 
                           params={"symbol": "SOLUSDT", "interval": "1h", "limit": 30}, 
                           timeout=10)
        dados = resp.json()
        closes = [float(x[4]) for x in dados]
        preco_atual = closes[-1]

        # Médias Móveis
        sma5 = sum(closes[-5:]) / 5
        sma21 = sum(closes[-21:]) / 21
        sma5_ant = sum(closes[-6:-1]) / 5

        # Lógica de Cruzamento
        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            msg = f"🟢 <b>COMPRA SOLUSDT</b>\nPreço: ${preco_atual:.2f}"
            enviar_telegram(msg)
            ultimo_sinal = "COMPRA"
            return "Sinal de COMPRA enviado!"
            
        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            msg = f"🔴 <b>VENDA SOLUSDT</b>\nPreço: ${preco_atual:.2f}"
            enviar_telegram(msg)
            ultimo_sinal = "VENDA"
            return "Sinal de VENDA enviado!"
        
        return f"Sem sinal agora. Preço: ${preco_atual:.2f} | SMA5: {sma5:.1f} | SMA21: {sma21:.1f}"

    except Exception as e:
        return f"Erro na análise: {e}"

# ==================== ROTAS FLASK ====================

@app.route('/')
def home():
    return "<h1>Bot SOLUSDT Ativo</h1><p>O monitoramento está rodando em background.</p>"

@app.route('/verificar')
def verificar_manual():
    resultado = logica_do_bot()
    return f"<h3>Resultado da Verificação:</h3><p>{resultado}</p>"

@app.route('/teste')
def teste():
    enviar_telegram("🧪 Teste do Railway - O Bot está vivo!")
    return "✅ Mensagem de teste enviada!"

# ==================== CONTROLE DE BACKGROUND ====================

def background_loop():
    while True:
        logica_do_bot()
        time.sleep(60) # Verifica a cada 1 minuto

if __name__ == '__main__':
    # Inicia a thread separada
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    # O Railway exige que a porta venha da variável de ambiente PORT
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta)
