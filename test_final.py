#!/usr/bin/env python3

import asyncio
import sys
import os

async def final_validation():
    try:
        from nq_trading_agent.data.ingestion import DataIngestion
        from nq_trading_agent.preprocessing.features import FeatureExtractor
        from nq_trading_agent.preprocessing.summarizer import DataSummarizer
        from nq_trading_agent.utils.llm_factory import LLMFactory
        
        print('🚀 NQ Trading Agent - Final Validation')
        print('=' * 45)
        
        # Data pipeline
        mock_config = {
            'source': 'mock',
            'nq': {'symbol': 'NQ', 'exchange': 'CME', 'tick_size': 0.25, 'tick_value': 5.0},
            'mock': {'volatility': 0.02, 'starting_price': 15000.0}
        }
        
        data_ingestion = DataIngestion(mock_config)
        await data_ingestion.connect()
        
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(hours=8)
        end = datetime.now()
        data = await data_ingestion.get_historical_data('NQ', start, end, '1h')
        current_price = data['close'].iloc[-1]
        
        print(f'✅ Data: {len(data)} NQ bars generated')
        print(f'   Current price: ${current_price:.2f}')
        
        # Feature extraction
        feature_config = {'indicators': {'sma': [20], 'rsi': [14]}, 'patterns': {'lookback_periods': 20}}
        feature_extractor = FeatureExtractor(feature_config)
        features = feature_extractor.extract_all_features(data)
        
        print(f'✅ Features: {len(features)} categories extracted')
        
        # Summarization
        summarizer_config = {'max_tokens': 120}
        data_summarizer = DataSummarizer(summarizer_config)
        summary = data_summarizer.summarize_features(features, data)
        
        print(f'✅ Summary: {len(summary)} character summary')
        
        # LLM setup with available model
        llm_config = {'provider': 'ollama', 'ollama': {'model': 'phi3:mini', 'host': 'http://localhost:11434'}}
        llm_provider = LLMFactory.create_provider(llm_config)
        
        print('✅ LLM: Phi3-mini model ready')
        
        # Trading prompt
        nq_config = {'tick_size': 0.25, 'tick_value': 5.0}
        prompt = data_summarizer.create_trading_prompt(summary, current_price, nq_config)
        
        print(f'✅ Prompt: {len(prompt)} characters')
        
        # LLM analysis
        print()
        print('🤖 Running AI analysis...')
        response = await llm_provider.generate_response(prompt)
        signal = data_summarizer.parse_llm_response(response)
        
        print(f'✅ AI Analysis complete!')
        print(f'   Action: {signal["action"]}')
        print(f'   Confidence: {signal["confidence"]}/10')
        
        if signal.get('reasoning'):
            reasoning = signal['reasoning'][:80] + '...' if len(signal['reasoning']) > 80 else signal['reasoning']
            print(f'   Reasoning: {reasoning}')
        
        # Platform test
        from nq_trading_agent.platforms.mock_platform import MockPlatform
        platform = MockPlatform({'initial_balance': 100000.0})
        await platform.connect()
        
        print('✅ Trading platform: Mock platform connected')
        
        # Cleanup
        await data_ingestion.disconnect()
        await platform.disconnect()
        
        print()
        print('🎉 VALIDATION COMPLETE - ALL SYSTEMS OPERATIONAL!')
        print()
        print('📊 Final Results:')
        print(f'   📈 NQ Futures Price: ${current_price:.2f}')
        print(f'   🎯 AI Trading Decision: {signal["action"]}')
        print(f'   📊 Confidence Level: {signal["confidence"]}/10')
        print(f'   📋 Features Analyzed: {len(features)} categories')
        print(f'   📄 Data Points: {len(data)} OHLCV bars')
        
        print()
        print('✅ System Components Verified:')
        print('   • Mock NQ data generation ✓')
        print('   • Technical analysis features ✓') 
        print('   • AI-powered decision making ✓')
        print('   • Trading signal parsing ✓')
        print('   • Mock trading platform ✓')
        
        print()
        print('🚀 NQ Trading Agent is READY!')
        print('   Next: Add API keys for live trading')
        
        return True
        
    except Exception as e:
        print(f'❌ Validation failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(final_validation())
    print(f'\n📋 Final Status: {"SUCCESS" if result else "FAILED"}')