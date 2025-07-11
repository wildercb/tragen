#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
from datetime import datetime

def check_real_nq_price():
    try:
        print('🔍 Checking Real NQ Futures Price...')
        print('=' * 40)
        
        # Get NQ futures ticker
        nq = yf.Ticker('NQ=F')
        
        # Get current info
        info = nq.info
        current_price = info.get('regularMarketPrice', info.get('previousClose', 0))
        
        print(f'📊 NQ Futures Current Price: ${current_price:,.2f}')
        
        # Get recent trading data
        print('\n📈 Fetching recent NQ data...')
        data = nq.history(period='1d', interval='5m')
        
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            high = data['High'].max()
            low = data['Low'].min()
            
            print(f'✅ Real NQ Data Retrieved!')
            print(f'   Latest Close: ${latest_price:,.2f}')
            print(f'   Day High: ${high:,.2f}')
            print(f'   Day Low: ${low:,.2f}')
            print(f'   Data Points: {len(data)} bars')
            print(f'   Last Update: {data.index[-1]}')
            
            # Show data structure
            print(f'\n📋 Data Structure:')
            print(f'   Columns: {list(data.columns)}')
            print(f'   Index type: {type(data.index)}')
            
            # Show recent bars
            print(f'\n📊 Recent 5-min NQ Bars:')
            recent = data.tail(5)
            for idx, row in recent.iterrows():
                time_str = idx.strftime('%H:%M')
                print(f'   {time_str}: ${row["Close"]:,.2f} (H: ${row["High"]:,.2f}, L: ${row["Low"]:,.2f})')
            
            # Verify this is reasonable NQ price
            if latest_price > 20000:
                print(f'\n✅ CONFIRMED: Real NQ price ${latest_price:,.2f} matches current market levels')
                return True, latest_price, data
            else:
                print(f'\n⚠️ WARNING: Price ${latest_price:,.2f} seems unusually low')
                return False, latest_price, data
        else:
            print('❌ No data available - market may be closed')
            return False, 0, pd.DataFrame()
            
    except Exception as e:
        print(f'❌ Error checking NQ price: {e}')
        return False, 0, pd.DataFrame()

if __name__ == "__main__":
    success, price, data = check_real_nq_price()
    print(f'\n📋 Result: {"SUCCESS" if success else "FAILED"} - Price: ${price:,.2f}')