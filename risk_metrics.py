import numpy as np
import pandas as pd
from typing import Dict, List

class RiskMetrics:
    def __init__(self, returns: pd.DataFrame):
        self.returns = returns
        self.cumulative_returns = (1 + returns).cumprod()
    
    def calculate_var(self, weights: np.ndarray, alpha: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR) for the portfolio
        """
        portfolio_returns = (self.returns * weights).sum(axis=1)
        return np.percentile(portfolio_returns, alpha * 100)
    
    def calculate_cvar(self, weights: np.ndarray, alpha: float = 0.05) -> float:
        """
        Calculate Conditional Value at Risk (CVaR)
        """
        portfolio_returns = (self.returns * weights).sum(axis=1)
        var = self.calculate_var(weights, alpha)
        return portfolio_returns[portfolio_returns <= var].mean()
    
    def calculate_beta(self, weights: np.ndarray, market_returns: pd.Series) -> float:
        """
        Calculate portfolio beta relative to market
        """
        portfolio_returns = (self.returns * weights).sum(axis=1)
        cov_matrix = np.cov(portfolio_returns, market_returns)
        return cov_matrix[0, 1] / cov_matrix[1, 1]
    
    def calculate_drawdown(self, weights: np.ndarray) -> Dict:
        """
        Calculate maximum drawdown and duration
        """
        portfolio_returns = (self.returns * weights).sum(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        
        max_drawdown = drawdown.min()
        max_drawdown_period = drawdown.idxmin()
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_period': max_drawdown_period,
            'drawdown_series': drawdown
        }
    
    def calculate_rolling_volatility(self, weights: np.ndarray, window: int = 21) -> pd.Series:
        """
        Calculate rolling volatility (standard deviation)
        """
        portfolio_returns = (self.returns * weights).sum(axis=1)
        return portfolio_returns.rolling(window=window).std() * np.sqrt(252)
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """
        Calculate correlation matrix between assets
        """
        return self.returns.corr()