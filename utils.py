import pandas as pd
import numpy as np
from typing import List, Dict

def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate log returns from price data
    """
    return np.log(prices / prices.shift(1)).dropna()

def calculate_simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate simple returns from price data
    """
    return prices.pct_change().dropna()

def format_weights(weights: np.ndarray, assets: List[str]) -> Dict:
    """
    Format weights into a dictionary with asset names
    """
    return {asset: weight for asset, weight in zip(assets, weights)}

def format_percentage(value: float) -> str:
    """
    Format float as percentage string
    """
    return f"{value*100:.2f}%"

def annualize_return(daily_return: float, periods: int = 252) -> float:
    """
    Annualize daily return
    """
    return (1 + daily_return) ** periods - 1

def annualize_volatility(daily_vol: float, periods: int = 252) -> float:
    """
    Annualize daily volatility
    """
    return daily_vol * np.sqrt(periods)