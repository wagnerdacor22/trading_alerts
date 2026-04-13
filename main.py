def logica_do_bot():
    global ultimo_sinal
    agora = datetime.now().strftime('%H:%M:%S')
    
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "SOLUSDT", "interval": "1h", "limit": 100} 
        resp = requests.get(url, params=params, timeout=10)
        dados = resp.json()
        df = pd.DataFrame(dados, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df['close'] = df['close'].astype(float)

        # --- CÁLCULOS ---
        df['ema5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['sma21'] = df['close'].rolling(window=21).mean()
        
        # Cálculo da Volatilidade (Bandas de Bollinger)
        df['stddev'] = df['close'].rolling(window=21).std()
        df['upper'] = df['sma21'] + (2 * df['stddev'])
        df['lower'] = df['sma21'] - (2 * df['stddev'])
        # Largura das bandas em porcentagem
        df['bandwidth'] = ((df['upper'] - df['lower']) / df['sma21']) * 100

        atual_ema5 = df['ema5'].iloc[-1]
        atual_sma21 = df['sma21'].iloc[-1]
        bw_atual = df['bandwidth'].iloc[-1]
        preco_atual = df['close'].iloc[-1]

        # O Filtro que você definiu
        filtro_lateral = 1.535
        mercado_vivo = bw_atual > filtro_lateral

        status = f"Preço: {preco_atual:.2f} | BW: {bw_atual:.3f}% | {'✅ ATIVO' if mercado_vivo else '💤 LATERAL'}"
        print(f"[{agora}] {status}", flush=True)

        # --- LÓGICA DE SINAL ---
        if mercado_vivo:
            # Compra: EMA5 cruza pra cima da SMA21
            if atual_ema5 > atual_sma21 and ultimo_sinal != "COMPRA":
                msg = f"🟢 <b>SOL COMPRA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}% (Rompimento!)"
                enviar_telegram(msg)
                ultimo_sinal = "COMPRA"
            
            # Venda: EMA5 cruza pra baixo da SMA21
            elif atual_ema5 < atual_sma21 and ultimo_sinal != "VENDA":
                msg = f"🔴 <b>SOL VENDA (1H)</b>\n💰 Preço: {preco_atual:.2f}\n📊 Bandwidth: {bw_atual:.3f}% (Rompimento!)"
                enviar_telegram(msg)
                ultimo_sinal = "VENDA"
        
        return status

    except Exception as e:
        print(f"❌ Erro: {e}")
        return f"Erro: {str(e)}"
