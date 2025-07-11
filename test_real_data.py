#!/usr/bin/env python3

import asyncio
import sys
import os

async def test_real_nq_data():
    try:
        from nq_trading_agent.data.ingestion import DataIngestion
        from nq_trading_agent.preprocessing.features import FeatureExtractor
        from nq_trading_agent.preprocessing.summarizer import DataSummarizer
        from nq_trading_agent.utils.llm_factory import LLMFactory
        
        print('🔍 Testing with REAL NQ Futures Data')
        print('=' * 50)
        
        # Yahoo Finance config for real NQ data
        yahoo_config = {
            'source': 'yahoo',
            'nq': {'symbol': 'NQ', 'exchange': 'CME', 'tick_size': 0.25, 'tick_value': 5.0},
            'yahoo': {'symbol': 'NQ=F', 'interval': '1m'}
        }
        
        data_ingestion = DataIngestion(yahoo_config)
        await data_ingestion.connect()
        
        # Get recent real data
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(hours=4)  # Last 4 hours
        end = datetime.now()
        
        print(f'📊 Fetching real NQ data from {start.strftime("%H:%M")} to {end.strftime("%H:%M")}...')
        data = await data_ingestion.get_historical_data('NQ=F', start, end, '1m')
        
        if data.empty:
            print('❌ No data received - market may be closed')
            return False
            
        current_price = data['close'].iloc[-1]
        high_price = data['high'].max()
        low_price = data['low'].min()
        
        print(f'✅ REAL NQ DATA RECEIVED!')
        print(f'   📈 Current NQ Price: ${current_price:,.2f}')
        print(f'   📊 Session High: ${high_price:,.2f}')
        print(f'   📉 Session Low: ${low_price:,.2f}')
        print(f'   📋 Data Points: {len(data)} bars')
        print(f'   ⏰ Latest Update: {data.index[-1]}')
        
        # Verify this is real data (should be around 23,000 as you mentioned)
        if current_price > 20000:
            print(f'✅ CONFIRMED: Real NQ price ~${current_price:,.0f} (matches current market)')
        else:
            print(f'⚠️  WARNING: Price ${current_price:,.2f} seems low for current NQ')
        
        # Extract features from real data
        feature_config = {
            'indicators': {'sma': [20], 'rsi': [14], 'atr': [14]},
            'patterns': {'lookback_periods': 20}
        }
        
        feature_extractor = FeatureExtractor(feature_config)
        features = feature_extractor.extract_all_features(data)
        
        print(f'✅ Features extracted from real data: {len(features)} categories')
        
        # Create summary of real market conditions
        summarizer_config = {'max_tokens': 200}
        data_summarizer = DataSummarizer(summarizer_config)
        summary = data_summarizer.summarize_features(features, data)
        
        print(f'✅ Real market summary: {len(summary)} chars')
        print(f'   📄 Summary: {summary[:100]}...')
        
        # Setup Ollama with real data
        llm_config = {
            'provider': 'ollama', 
            'ollama': {'model': 'phi3:mini', 'host': 'http://localhost:11434'}
        }
        
        llm_provider = LLMFactory.create_provider(llm_config)
        
        # Create trading prompt with real data
        nq_config = {'tick_size': 0.25, 'tick_value': 5.0}
        prompt = data_summarizer.create_trading_prompt(summary, current_price, nq_config)
        
        print()
        print('🤖 Analyzing REAL NQ market with Ollama...')
        print(f'   💰 Analyzing NQ at ${current_price:,.2f}')
        
        # Get AI analysis of real market
        response = await llm_provider.generate_response(prompt)
        signal = data_summarizer.parse_llm_response(response)
        
        print()
        print('🎯 REAL MARKET ANALYSIS COMPLETE!')
        print(f'   📈 Current NQ Price: ${current_price:,.2f}')
        print(f'   🤖 AI Decision: {signal["action"]}')
        print(f'   📊 Confidence: {signal["confidence"]}/10')
        
        if signal.get('reasoning'):
            reasoning = signal['reasoning'][:150] + '...' if len(signal['reasoning']) > 150 else signal['reasoning']
            print(f'   💭 AI Reasoning: {reasoning}')
        
        if signal.get('entry_price'):
            print(f'   💰 Suggested Entry: ${signal["entry_price"]:,.2f}')
        if signal.get('stop_loss'):
            print(f'   🛡️  Stop Loss: ${signal["stop_loss"]:,.2f}')
        if signal.get('take_profit'):
            print(f'   🎯 Take Profit: ${signal["take_profit"]:,.2f}')
        
        # Show recent price action
        print()
        print('📊 Recent NQ Price Action:')
        recent_data = data.tail(5)
        for idx, row in recent_data.iterrows():
            time_str = idx.strftime('%H:%M')
            print(f'   {time_str}: Open ${row["open"]:,.2f} | High ${row["high"]:,.2f} | Low ${row["low"]:,.2f} | Close ${row["close"]:,.2f}')
        
        await data_ingestion.disconnect()
        
        print()
        print('✅ REAL DATA VALIDATION COMPLETE!')
        print(f'   🎯 NQ Trading Agent successfully analyzed REAL market data')
        print(f'   📈 Current NQ: ${current_price:,.2f}')
        print(f'   🤖 AI Signal: {signal["action"]} with {signal["confidence"]}/10 confidence')
        
        return True
        
    except Exception as e:
        print(f'❌ Real data test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_real_nq_data())
    print(f'\n📋 Real Data Test: {"SUCCESS" if result else "FAILED"}')