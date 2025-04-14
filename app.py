import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
from portfolio_optimizer import PortfolioOptimizer
from risk_metrics import RiskMetrics
from data_fetcher import DataFetcher
from portfolio_calculations import calculate_portfolio_value
from utils import (
    calculate_simple_returns,
    format_weights,
    format_percentage,
    annualize_return,
    annualize_volatility
)

# Page configuration
st.set_page_config(
    page_title="Portfolio Optimizer & Risk Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stDownloadButton>button {
        background-color: #2196F3;
        color: white;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .asset-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'tickers' not in st.session_state:
    st.session_state.tickers = []
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'returns_data' not in st.session_state:
    st.session_state.returns_data = None

# Initialize data fetcher
fetcher = DataFetcher()

# Sidebar - Input parameters
st.sidebar.title("Portfolio Inputs")

# Date range selection
end_date = datetime.today()
start_date = end_date - timedelta(days=365 * 3)  # Default 3 years

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", start_date)
with col2:
    end_date = st.date_input("End Date", end_date)

# Ticker input
st.sidebar.subheader("Asset Selection")
ticker_input = st.sidebar.text_input("Enter ticker symbol (e.g., AAPL)", "")

if ticker_input:
    search_results = fetcher.get_available_tickers(ticker_input)
    if search_results:
        selected_ticker = st.sidebar.selectbox("Select from available tickers", search_results)
        if st.sidebar.button("Add to portfolio"):
            if selected_ticker not in st.session_state.tickers:
                st.session_state.tickers.append(selected_ticker)
                st.sidebar.success(f"Added {selected_ticker} to portfolio")
            else:
                st.sidebar.warning(f"{selected_ticker} is already in the portfolio")
    else:
        st.sidebar.warning("No tickers found. Please try another symbol.")

st.sidebar.subheader("Share Holdings")
holdings = {}
if st.session_state.tickers:
    for ticker in st.session_state.tickers:
        holdings[ticker] = st.sidebar.number_input(
            f"Shares of {ticker}",
            min_value=0,
            value=100,  # Default value
            key=f"shares_{ticker}"
        )

# Display current portfolio
if st.session_state.tickers:
    st.sidebar.subheader("Current Portfolio")
    for i, ticker in enumerate(st.session_state.tickers):
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.write(ticker)
        with col2:
            if st.button("×", key=f"remove_{i}"):
                st.session_state.tickers.remove(ticker)
                st.session_state.price_data = None
                st.session_state.returns_data = None
                st.experimental_rerun()
    
    if st.sidebar.button("Clear Portfolio"):
        st.session_state.tickers = []
        st.session_state.price_data = None
        st.session_state.returns_data = None
        st.experimental_rerun()

# Fetch data button
# Fetch data button
if st.session_state.tickers and st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching price data..."):
        try:
            price_data = fetcher.fetch_yfinance_data(
                st.session_state.tickers,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            st.session_state.price_data = price_data
            st.session_state.returns_data = calculate_simple_returns(price_data)
            
            # Get current prices for holdings calculation
            current_prices = fetcher.get_current_prices(st.session_state.tickers)
            st.session_state.current_prices = current_prices
            st.session_state.holdings = holdings
            
            st.sidebar.success("Data fetched successfully!")
        except Exception as e:
            st.sidebar.error(f"Error fetching data: {str(e)}")

# Main content
st.title("📊 Portfolio Optimizer & Risk Dashboard")

if not st.session_state.tickers:
    st.info("Please add assets to your portfolio using the sidebar.")
    st.stop()

if st.session_state.price_data is None:
    st.warning("Click 'Fetch Data' in the sidebar to load price data.")
    st.stop()

# Display price chart
st.subheader("Asset Price Trends")
fig = px.line(st.session_state.price_data, title="Normalized Price History")
fig.update_layout(height=500, xaxis_title="Date", yaxis_title="Price (Normalized)")
st.plotly_chart(fig, use_container_width=True)

# Portfolio optimization section
st.subheader("Portfolio Optimization")

# Create optimizer and risk metrics instances
optimizer = PortfolioOptimizer(st.session_state.returns_data)
risk_metrics = RiskMetrics(st.session_state.returns_data)

# Calculate equal weight portfolio first
equal_weight_result = optimizer.equal_weight_portfolio()

# Optimization strategy selection
risk_free_rate = st.number_input(
    "Risk-Free Rate (%)", 
    min_value=0.0, 
    max_value=20.0, 
    value=2.0, 
    step=0.1
) / 100
strategy = st.selectbox(
    "Optimization Strategy",
    ["Equal Weight", "Minimum Variance", "Maximum Sharpe Ratio"]
)

# ====== NEW CODE STARTS HERE ======
from portfolio_calculations import calculate_portfolio_value

# Calculate initial weights based on holdings
if 'holdings' in st.session_state and 'current_prices' in st.session_state:
    holdings_data = calculate_portfolio_value(
        st.session_state.holdings,
        st.session_state.current_prices
    )
    initial_weights = holdings_data['weights']
else:
    initial_weights = None

# Add a checkbox to choose between custom weights and optimization
use_custom_weights = st.checkbox("Use my current shareholdings as weights", value=True)

if use_custom_weights and initial_weights is not None:
    result = {
        'weights': initial_weights,
        'return': np.sum(st.session_state.returns_data.mean() * initial_weights),
        'volatility': np.sqrt(np.dot(initial_weights.T, 
                                   np.dot(st.session_state.returns_data.cov(), 
                                          initial_weights)))
    }
    st.info("Using your current shareholdings to calculate portfolio weights")
else:
    # Original optimization code
    if strategy == "Equal Weight":
        result = optimizer.equal_weight_portfolio()
    elif strategy == "Minimum Variance":
        result = optimizer.min_variance()
    elif strategy == "Maximum Sharpe Ratio":
        result = optimizer.max_sharpe_ratio(risk_free_rate)
# ====== NEW CODE ENDS HERE ======

# Display optimization results
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Expected Annual Return", 
              format_percentage(annualize_return(result['return'])))
with col2:
    st.metric("Annual Volatility", 
              format_percentage(annualize_volatility(result['volatility'])))
with col3:
    if 'sharpe_ratio' in result:
        st.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
    # ====== NEW PORTFOLIO VALUE DISPLAY ======
if 'holdings' in st.session_state and 'current_prices' in st.session_state:
    total_value = sum(
        st.session_state.holdings[ticker] * st.session_state.current_prices[ticker] 
        for ticker in st.session_state.tickers 
        if ticker in st.session_state.current_prices
    )
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
# ====== NEW CODE ENDS HERE ======

# Display portfolio weights
st.subheader("Portfolio Allocation")
weights = format_weights(result['weights'], st.session_state.tickers)

fig = px.pie(
    names=list(weights.keys()),
    values=list(weights.values()),
    title="Portfolio Weights"
)
st.plotly_chart(fig, use_container_width=True)

# Show weights in a table
weights_df = pd.DataFrame.from_dict(weights, orient='index', columns=['Weight'])
weights_df['Weight'] = weights_df['Weight'].apply(lambda x: format_percentage(x))
st.dataframe(weights_df, use_container_width=True)

# Risk metrics section
st.subheader("Risk Analysis")

# Calculate risk metrics
var = risk_metrics.calculate_var(result['weights'])
cvar = risk_metrics.calculate_cvar(result['weights'])
drawdown = risk_metrics.calculate_drawdown(result['weights'])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Value at Risk (95%)", format_percentage(var))
with col2:
    st.metric("Conditional VaR (95%)", format_percentage(cvar))
with col3:
    st.metric("Max Drawdown", format_percentage(drawdown['max_drawdown']))

# Drawdown chart
st.subheader("Portfolio Drawdown")
fig = px.area(
    drawdown['drawdown_series'],
    title="Historical Drawdown",
    labels={'value': 'Drawdown', 'index': 'Date'}
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Efficient frontier
st.subheader("Efficient Frontier")
st.write("""
The efficient frontier shows optimal portfolios that offer the highest expected return 
for a given level of risk or the lowest risk for a given level of return.
""")

# Generate efficient frontier
target_returns = np.linspace(
    st.session_state.returns_data.min().min(),
    st.session_state.returns_data.max().max(),
    20
)
efficient_portfolios = optimizer.efficient_frontier(target_returns)

if efficient_portfolios:
    frontier_data = pd.DataFrame([{
        'Return': annualize_return(p['return']),
        'Volatility': annualize_volatility(p['volatility']),
        'Weights': p['weights']
    } for p in efficient_portfolios])
    
    # Add current portfolio to the plot
    current_portfolio = pd.DataFrame([{
        'Return': annualize_return(result['return']),
        'Volatility': annualize_volatility(result['volatility']),
        'Label': 'Current Portfolio'
    }])
    
    fig = px.scatter(
        frontier_data,
        x='Volatility',
        y='Return',
        title="Efficient Frontier",
        labels={'Volatility': 'Annualized Volatility', 'Return': 'Annualized Return'}
    )
    
    # Add current portfolio marker
    fig.add_scatter(
        x=current_portfolio['Volatility'],
        y=current_portfolio['Return'],
        mode='markers',
        marker=dict(color='red', size=12),
        name='Current Portfolio',
        hovertext='Current Portfolio'
    )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

# Correlation matrix
st.subheader("Asset Correlation Matrix")
corr_matrix = risk_metrics.calculate_correlation_matrix()
fig = px.imshow(
    corr_matrix,
    text_auto=True,
    aspect="auto",
    color_continuous_scale='RdBu',
    range_color=[-1, 1],
    title="Correlation Between Assets"
)
st.plotly_chart(fig, use_container_width=True)

# Rolling volatility
st.subheader("Rolling Volatility (21-day)")
rolling_vol = risk_metrics.calculate_rolling_volatility(result['weights'])
fig = px.line(
    rolling_vol,
    title="Rolling Volatility",
    labels={'value': 'Volatility', 'index': 'Date'}
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# Download results
st.subheader("Export Results")
if st.button("Download Portfolio Allocation"):
    weights_df = pd.DataFrame.from_dict(weights, orient='index', columns=['Weight'])
    csv = weights_df.to_csv().encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="portfolio_allocation.csv",
        mime="text/csv"
    )