"""
Test the Market Context Analyzer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_trading_agent.market_context import market_analyzer
from datetime import datetime, timedelta
import random

# Generate sample OHLCV data
def generate_sample_data():
    data = []
    base_price = 20000
    current_time = datetime.now()
    
    for i in range(100):
        time_stamp = current_time - timedelta(minutes=i*5)
        
        # Generate realistic price movement
        price_change = random.uniform(-0.5, 0.5) / 100 * base_price
        open_price = base_price
        close_price = base_price + price_change
        high_price = max(open_price, close_price) + random.uniform(0, 0.2) / 100 * base_price
        low_price = min(open_price, close_price) - random.uniform(0, 0.2) / 100 * base_price
        
        # Create Fair Value Gap occasionally
        if i % 20 == 0:
            # Create a gap
            gap_size = random.uniform(0.1, 0.3) / 100 * base_price
            if random.choice([True, False]):
                # Bullish gap
                low_price = high_price + gap_size
                close_price = low_price + random.uniform(0, 0.1) / 100 * base_price
            else:
                # Bearish gap
                high_price = low_price - gap_size
                close_price = high_price - random.uniform(0, 0.1) / 100 * base_price
        
        data.append({
            'time': int(time_stamp.timestamp()),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': random.randint(1000, 10000)
        })
        
        base_price = close_price
    
    return list(reversed(data))  # Reverse to get chronological order

if __name__ == "__main__":
    print("🧪 Testing Market Context Analyzer...\n")
    
    # Generate sample data
    sample_data = generate_sample_data()
    print(f"Generated {len(sample_data)} sample candles")
    
    # Analyze market context
    print("\n🔍 Analyzing market context...")
    context = market_analyzer.analyze_market_context(sample_data)
    
    # Format for AI
    print("\n📝 Formatted context for AI:")
    print("=" * 80)
    formatted_context = market_analyzer.format_context_for_ai(context)
    print(formatted_context)
    print("=" * 80)
    
    # Show raw context structure
    print("\n🔧 Raw context structure:")
    for key, value in context.items():
        if key == 'trading_sessions':
            print(f"  {key}: {len(value)} sessions")
        elif key == 'fair_value_gaps':
            bullish_count = len(value['bullish'])
            bearish_count = len(value['bearish'])
            print(f"  {key}: {bullish_count} bullish, {bearish_count} bearish")
        elif key == 'order_blocks':
            bullish_count = len(value['bullish'])
            bearish_count = len(value['bearish'])
            print(f"  {key}: {bullish_count} bullish, {bearish_count} bearish")
        elif key == 'liquidity_zones':
            buy_count = len(value['buy_side'])
            sell_count = len(value['sell_side'])
            print(f"  {key}: {buy_count} buy-side, {sell_count} sell-side")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    print("\n✅ Market Context Analyzer test complete!")