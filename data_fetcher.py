import yfinance as yf
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict

load_dotenv()

class DataFetcher:
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '57PTG52IHJUJG5GH')
        if self.alpha_vantage_key:
            self.ts = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
    
    def fetch_yfinance_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Ultra-reliable Yahoo Finance data fetcher with comprehensive error handling"""
        try:
            # Validate inputs
            if not tickers:
                raise ValueError("No tickers provided")
            
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            if start_dt >= end_dt:
                raise ValueError("Start date must be before end date")

            # We'll fetch each ticker individually for maximum reliability
            all_data = {}
            
            for ticker in tickers:
                try:
                    # First try with auto_adjust=True
                    ticker_obj = yf.Ticker(ticker)
                    df = ticker_obj.history(
                        start=start_date,
                        end=end_date,
                        auto_adjust=True,
                        actions=False
                    )
                    
                    # If empty, try without auto_adjust
                    if df.empty:
                        df = ticker_obj.history(
                            start=start_date,
                            end=end_date,
                            auto_adjust=False,
                            actions=False
                        )
                    
                    # If still empty, try different period parameter
                    if df.empty:
                        df = ticker_obj.history(
                            period="max",
                            auto_adjust=True,
                            actions=False
                        )
                        # Filter to our desired date range
                        df = df.loc[start_date:end_date]
                    
                    # Verify we got data
                    if df.empty:
                        raise ValueError(f"No data available for {ticker} in date range")
                    
                    # Find the best available price column
                    price_columns = ['Close', 'Adj Close', 'Open', 'High', 'Low']
                    available_columns = [col for col in price_columns if col in df.columns]
                    
                    if not available_columns:
                        raise ValueError(f"No price columns found for {ticker}")
                    
                    # Use the first available price column
                    price_col = available_columns[0]
                    all_data[ticker] = df[price_col]
                    
                except Exception as e:
                    raise ValueError(f"Failed to fetch {ticker}: {str(e)}")
            
            # Combine all tickers into a single DataFrame
            result = pd.DataFrame(all_data)
            
            if result.empty:
                raise ValueError("No data available for any ticker")
                
            return result.dropna()
        
        except Exception as e:
            raise Exception(f"Error fetching Yahoo Finance data: {str(e)}")
    
    def fetch_alpha_vantage_data(self, tickers: List[str]) -> Optional[pd.DataFrame]:
        """Fetch current price data from Alpha Vantage."""
        try:
            if not hasattr(self, 'ts') or not self.alpha_vantage_key:
                return None
                
            prices = {}
            
            for ticker in tickers:
                try:
                    data, _ = self.ts.get_quote_endpoint(symbol=ticker)
                    prices[ticker] = float(data['05. price'])
                except Exception as e:
                    print(f"Error fetching {ticker} from Alpha Vantage: {str(e)}")
                    continue
            
            return pd.DataFrame.from_dict(prices, orient='index', columns=['price']) if prices else None
        
        except Exception as e:
            print(f"Error in Alpha Vantage fetch: {str(e)}")
            return None
    
    def get_available_tickers(self, query: str) -> List[str]:
        try:
            ticker = yf.Ticker(query)
            info = ticker.info
            if info and 'symbol' in info:
                return [info['symbol']]
            return [query]
        except Exception as e:
            print(f"Error searching for tickers: {str(e)}")
            return [query]
    
    def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current market prices for tickers"""
        prices = {}
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker).history(period='1d')
                if not data.empty and 'Close' in data.columns:
                    prices[ticker] = data['Close'].iloc[-1]
            except Exception as e:
                print(f"Couldn't fetch price for {ticker}: {str(e)}")
        return prices