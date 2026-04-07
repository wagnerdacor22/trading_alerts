def logica_do_bot():
    global ultimo_sinal
    try:
        # 1. Tenta a requisição com timeout curto
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 30}
        
        response = requests.get(url, params=params, timeout=5)
        
        # Verificação de status da resposta
        if response.status_code != 200:
            return f"Erro na Binance: Status {response.status_code} - {response.text}"

        dados = response.json()
        
        # 2. Verifica se os dados vieram no formato esperado (lista de listas)
        if not isinstance(dados, list):
            return f"Erro: Binance não retornou uma lista. Retorno: {dados}"

        closes = [float(x[4]) for x in dados]
        preco = closes[-1]

        # Médias móveis
        sma5 = sum(closes[-5:]) / 5
        sma21 = sum(closes[-21:]) / 21
        sma5_ant = sum(closes[-6:-1]) / 5

        resultado = f"Preço: {preco} | SMA5: {sma5:.2f} | SMA21: {sma21:.2f}"
        
        # Lógica de Sinais
        if sma5_ant < sma21 and sma5 >= sma21 and ultimo_sinal != "COMPRA":
            enviar_telegram(f"🟢 COMPRA SOLUSDT\nPreço: {preco}")
            ultimo_sinal = "COMPRA"
        elif sma5_ant > sma21 and sma5 <= sma21 and ultimo_sinal != "VENDA":
            enviar_telegram(f"🔴 VENDA SOLUSDT\nPreço: {preco}")
            ultimo_sinal = "VENDA"
            
        return resultado

    except Exception as e:
        # Isso vai te mostrar o erro real na tela do navegador
        import traceback
        erro_detalhado = traceback.format_exc()
        print(f"ERRO CRÍTICO: {erro_detalhado}")
        return f"Erro na lógica: {str(e)}"
