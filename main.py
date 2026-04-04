from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Pega variáveis de ambiente (vamos configurar no Railway)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def formatar_alerta(data):
    tipo = data.get('tipo', 'desconhecido')
    acao = data.get('acao', '').upper()
    
    if tipo == 'pre_sinal':
        emoji = "🟡" if data['acao'] == 'compra' else "🟠"
        return f"""{emoji} <b>ALERTA: PRÓXIMO DE {acao}</b> {emoji}

📊 <b>Ativo:</b> {data.get('simbolo', 'N/A')}
⏰ <b>Timeframe:</b> {data.get('timeframe', 'N/A')}
💰 <b>Preço:</b> {data.get('preco_atual', 'N/A')}
📈 <b>EMA 5:</b> {data.get('ema5', 0):.2f}
📊 <b>BB Central:</b> {data.get('bb_central', 0):.2f}

⚠️ <i>{data.get('mensagem', '')}</i>"""
    else:
        emoji = "🟢" if data['acao'] == 'compra' else "🔴"
        return f"""{emoji} <b>SINAL CONFIRMADO: {acao}</b> {emoji}

📊 <b>Ativo:</b> {data.get('simbolo', 'N/A')}
⏰ <b>Timeframe:</b> {data.get('timeframe', 'N/A')}
💰 <b>Preço:</b> {data.get('preco_entrada', 'N/A')}
📈 <b>EMA 5:</b> {data.get('ema5', 0):.2f}
📊 <b>BB Central:</b> {data.get('bb_central', 0):.2f}

✅ <i>{data.get('mensagem', '')}</i>"""

@app.route('/')
def home():
    return "✅ Servidor TradingView → Telegram está online!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        mensagem = formatar_alerta(data)
        resultado = enviar_telegram(mensagem)
        return jsonify({"status": "ok", "telegram": resultado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/teste', methods=['GET'])
def teste():
    mensagem = "🧪 <b>Teste de conexão!</b>\n\nServidor está funcionando! ✅"
    resultado = enviar_telegram(mensagem)
    return jsonify({"status": "teste enviado", "result": resultado})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
