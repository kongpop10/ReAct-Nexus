"""Handles stock data retrieval functionalities."""

import os
import json
import requests
import streamlit as st

def get_stock_data(symbol: str = None, ticker: str = None, stock_symbol: str = None) -> str:
    """Fetches real-time stock data using Alpha Vantage API
    Accepts 'symbol', 'ticker', or 'stock_symbol' parameter for backward compatibility.
    """
    actual_symbol = symbol
    if actual_symbol is None:
        actual_symbol = ticker
    if actual_symbol is None:
        actual_symbol = stock_symbol

    st.write(f"TOOL: get_stock_data(symbol='{actual_symbol}')")

    if actual_symbol is None:
        return json.dumps({'error': 'No stock symbol provided. Please provide a symbol using one of these parameters: "symbol", "ticker", or "stock_symbol"'})

    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return json.dumps({'error': 'ALPHA_VANTAGE_API_KEY not found in environment variables'})

    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={actual_symbol}&apikey={api_key}'
        response = requests.get(url)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({'error': f'API request failed: {str(e)}'})