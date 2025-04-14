import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.optimize import minimize
from typing import Tuple, Dict, List

class PortfolioOptimizer:
    def __init__(self, returns: pd.DataFrame):
        # Clean data by dropping NA values
        self.returns = returns.dropna()
        if self.returns.empty:
            raise ValueError("No valid returns data after cleaning NA values")
            
        self.mean_returns = self.returns.mean()
        self.cov_matrix = self.returns.cov()
        self.num_assets = len(self.returns.columns)
        
    def calculate_portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float]:
        """Calculate portfolio return and volatility with input validation"""
        if weights is None:
            raise ValueError("Weights cannot be None")
            
        if np.any(np.isnan(weights)):
            raise ValueError("Weights contain NaN values")
            
        if not np.isclose(np.sum(weights), 1.0, atol=0.01):
            raise ValueError(f"Weights must sum to 1 (got {np.sum(weights)})")
            
        port_return = np.sum(self.mean_returns * weights)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        return float(port_return), float(port_vol)
    
    def efficient_frontier(self, target_returns: np.ndarray) -> List[Dict]:
        """Calculate efficient frontier with robust error handling"""
        efficient_portfolios = []
        
        # Validate target returns range
        min_return = self.mean_returns.min()
        max_return = self.mean_returns.max()
        target_returns = np.clip(target_returns, min_return, max_return)
        
        for target in target_returns:
            weights = cp.Variable(self.num_assets)
            risk = cp.quad_form(weights, self.cov_matrix.values)
            
            constraints = [
                cp.sum(weights) == 1,
                weights >= 0,
                self.mean_returns.values.T @ weights >= target
            ]
            
            problem = cp.Problem(cp.Minimize(risk), constraints)
            
            try:
                problem.solve()
                
                if problem.status in ["infeasible", "unbounded"]:
                    continue
                    
                w = weights.value
                if w is None:
                    continue
                    
                ret, vol = self.calculate_portfolio_performance(w)
                efficient_portfolios.append({
                    'return': ret,
                    'volatility': vol,
                    'weights': w
                })
                
            except Exception as e:
                print(f"Skipping target return {target} due to error: {str(e)}")
                continue
        
        return efficient_portfolios
    
    def equal_weight_portfolio(self) -> Dict:
        """
        Calculate equal weight portfolio performance
        """
        weights = np.array([1/self.num_assets] * self.num_assets)
        ret, vol = self.calculate_portfolio_performance(weights)
        
        return {
            'weights': weights,
            'return': ret,
            'volatility': vol
        }