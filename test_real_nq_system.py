#!/usr/bin/env python3

import asyncio
import sys
import os

async def test_real_nq_system():
    try:
        from nq_trading_agent.data.ingestion import DataIngestion
        from nq_trading_agent.preprocessing.features import FeatureExtractor
        from nq_trading_agent.preprocessing.summarizer import DataSummarizer
        from nq_trading_agent.utils.llm_factory import LLMFactory
        
        print('🚀 NQ Trading Agent - REAL MARKET TEST')
        print('=' * 50)
        
        # Yahoo Finance config for real NQ data
        yahoo_config = {
            'source': 'yahoo',
            'nq': {'symbol': 'NQ', 'exchange': 'CME', 'tick_size': 0.25, 'tick_value': 5.0},
            'yahoo': {'symbol': 'NQ=F', 'interval': '5m'}
        }
        
        data_ingestion = DataIngestion(yahoo_config)
        await data_ingestion.connect()
        
        # Get real NQ data from last few hours
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(hours=6)
        end = datetime.now()
        
        print(f'📊 Fetching REAL NQ data...')
        data = await data_ingestion.get_historical_data('NQ=F', start, end, '5m')
        
        if data.empty:
            print('❌ No data received - market may be closed')
            return False
            
        current_price = data['close'].iloc[-1]
        high_price = data['high'].max()
        low_price = data['low'].min()
        volume_total = data['volume'].sum()
        
        print(f'✅ REAL NQ FUTURES DATA LOADED!')
        print(f'   💰 Current Price: ${current_price:,.2f}')
        print(f'   📈 Session High: ${high_price:,.2f}')
        print(f'   📉 Session Low: ${low_price:,.2f}')
        print(f'   📊 Volume: {volume_total:,.0f}')
        print(f'   📋 Data Points: {len(data)} bars')
        print(f'   ⏰ Latest: {data.index[-1]}')
        
        # Verify this is real current market data
        if current_price > 22000:
            print(f'✅ CONFIRMED: Real market data - NQ @ ${current_price:,.2f}')
        else:
            print(f'⚠️ WARNING: Price seems low for current NQ market')
        
        # Extract features from real market data
        print(f'\n🔍 Analyzing REAL market conditions...')
        feature_config = {
            'indicators': {'sma': [20, 50], 'rsi': [14], 'atr': [14], 'bollinger': [20, 2]},
            'patterns': {'lookback_periods': 30, 'min_pattern_strength': 0.7}
        }
        
        feature_extractor = FeatureExtractor(feature_config)
        features = feature_extractor.extract_all_features(data)
        
        print(f'✅ Features extracted from REAL data: {len(features)} categories')
        
        # Show key technical indicators
        tech_indicators = features.get('technical_indicators', {})
        if tech_indicators:
            print(f'   📊 SMA 20: ${tech_indicators.get("sma_20", 0):,.2f}')
            print(f'   📊 RSI: {tech_indicators.get("rsi_14", 0):.1f}')
            print(f'   📊 ATR: ${tech_indicators.get("atr_14", 0):.2f}')
        
        # Create summary of REAL market conditions
        summarizer_config = {'max_tokens': 200, 'include_volume': True, 'include_momentum': True}
        data_summarizer = DataSummarizer(summarizer_config)
        summary = data_summarizer.summarize_features(features, data)
        
        print(f'✅ Real market summary created: {len(summary)} chars')
        print(f'   📄 Market Summary: {summary}')
        
        # Setup Ollama for real market analysis
        llm_config = {
            'provider': 'ollama', 
            'ollama': {'model': 'phi3:mini', 'host': 'http://localhost:11434', 'temperature': 0.1}
        }
        
        llm_provider = LLMFactory.create_provider(llm_config)
        
        # Create trading prompt with REAL market data
        nq_config = {'tick_size': 0.25, 'tick_value': 5.0}
        prompt = data_summarizer.create_trading_prompt(summary, current_price, nq_config)
        
        print(f'\n🤖 ANALYZING REAL NQ MARKET WITH AI...')
        print(f'   💰 Current NQ Price: ${current_price:,.2f}')
        print(f'   📊 Market Session: {data.index[0].strftime("%H:%M")} - {data.index[-1].strftime("%H:%M")}')
        
        # Get AI analysis of REAL market conditions
        response = await llm_provider.generate_response(prompt)
        signal = data_summarizer.parse_llm_response(response)
        
        print(f'\n🎯 REAL MARKET AI ANALYSIS COMPLETE!')
        print(f'=' * 50)
        print(f'📈 CURRENT NQ FUTURES: ${current_price:,.2f}')
        print(f'🤖 AI TRADING DECISION: {signal["action"]}')
        print(f'📊 CONFIDENCE LEVEL: {signal["confidence"]}/10')
        
        if signal.get('entry_price'):
            print(f'💰 ENTRY PRICE: ${signal["entry_price"]:,.2f}')
        if signal.get('stop_loss'):
            print(f'🛡️ STOP LOSS: ${signal["stop_loss"]:,.2f}')
        if signal.get('take_profit'):
            print(f'🎯 TAKE PROFIT: ${signal["take_profit"]:,.2f}')
        
        if signal.get('reasoning'):
            print(f'💭 AI REASONING:')
            reasoning = signal['reasoning']
            # Split reasoning into lines for better readability
            lines = reasoning.split('. ')
            for line in lines[:3]:  # Show first 3 sentences
                if line.strip():
                    print(f'   • {line.strip()}')
        
        # Show recent price action context
        print(f'\n📊 RECENT NQ PRICE ACTION:')
        recent_data = data.tail(6)
        for idx, row in recent_data.iterrows():
            time_str = idx.strftime('%H:%M')
            change = row['close'] - row['open']
            change_pct = (change / row['open']) * 100
            direction = '📈' if change > 0 else '📉' if change < 0 else '➡️'
            print(f'   {time_str}: ${row["close"]:,.2f} {direction} ({change:+.2f}, {change_pct:+.2f}%)')
        
        # Show market context
        total_range = high_price - low_price
        current_position = (current_price - low_price) / total_range * 100
        
        print(f'\n📈 MARKET CONTEXT:')
        print(f'   📊 Session Range: ${total_range:.2f} ({total_range/current_price*100:.2f}%)')
        print(f'   📍 Current Position: {current_position:.1f}% of range')
        
        await data_ingestion.disconnect()
        
        print(f'\n✅ REAL MARKET ANALYSIS COMPLETE!')
        print(f'🚀 NQ Trading Agent successfully analyzed LIVE market data')
        print(f'📈 Real NQ Price: ${current_price:,.2f}')
        print(f'🤖 AI Decision: {signal["action"]} ({signal["confidence"]}/10 confidence)')
        
        return True
        
    except Exception as e:
        print(f'❌ Real market test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_real_nq_system())
    print(f'\n📋 REAL MARKET TEST: {"SUCCESS" if result else "FAILED"}')