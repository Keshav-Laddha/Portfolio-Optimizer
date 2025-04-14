import numpy as np
from typing import Dict

def calculate_portfolio_value(holdings: Dict[str, int], prices: Dict[str, float]) -> Dict:
    """Calculate portfolio weights based on actual holdings"""
    total_value = sum(shares * prices[ticker] for ticker, shares in holdings.items())
    
    if total_value == 0:
        return {ticker: 0 for ticker in holdings.keys()}
    
    weights = {
        ticker: (shares * prices[ticker]) / total_value
        for ticker, shares in holdings.items()
    }
    
    return {
        'weights': np.array(list(weights.values())),
        'total_value': total_value,
        'current_prices': prices
    }