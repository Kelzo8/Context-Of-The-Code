import streamlit as st
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, UTC
import time
import os
from metrics_sdk import MetricsClient, SystemMetrics, CryptoMetrics

# Page config
st.set_page_config(
    page_title="Metrics Dashboard",
    layout="wide"
)

# Initialize the metrics client
API_URL = os.getenv('API_URL', 'http://localhost:5000')

if not API_URL:
    st.error("API_URL environment variable is not set. Please configure it in your Streamlit Cloud settings.")
    st.stop()

try:
    client = MetricsClient(
        base_url=API_URL,
        device_id=1
    )
except Exception as e:
    st.error(f"Failed to initialize metrics client: {str(e)}")
    st.stop()

# Add API status indicator
st.sidebar.markdown("### API Status")
try:
    # Try to get a single metric to test connection
    client.get_metrics(limit=1)
    st.sidebar.success(f"✅ Connected to API at {API_URL}")
except Exception as e:
    st.sidebar.error(f"❌ API Connection Failed: {str(e)}")
    if "localhost" in API_URL:
        st.sidebar.warning("""
        You're trying to connect to a localhost API which won't work in cloud deployment.
        Please deploy your API service and update the API_URL in Streamlit Cloud settings.
        """)

def create_gauge(value, title, min_val=0, max_val=100):
    """Create a gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': 'darkblue'},
            'steps': [
                {'range': [0, max_val*0.6], 'color': 'lightgray'},
                {'range': [max_val*0.6, max_val*0.8], 'color': 'gray'},
                {'range': [max_val*0.8, max_val], 'color': 'darkgray'}
            ]
        }
    ))
    fig.update_layout(height=250)
    return fig

def main():
    # Title
    st.title("System & Crypto Metrics Dashboard")
    
    # Live Metrics Section
    st.header("Live Metrics")
    
    # Create two columns for gauges
    col1, col2 = st.columns(2)
    
    try:
        # Get latest metrics
        metrics = client.get_metrics(limit=1)
        
        if metrics:
            latest = metrics[0]
            
            # RAM Usage Gauge
            with col1:
                ram_value = latest.system_metrics.ram_usage_percent if latest.system_metrics else 0
                st.plotly_chart(create_gauge(ram_value, 'RAM Usage %'), use_container_width=True)
            
            # Thread Count Gauge
            with col2:
                thread_value = latest.system_metrics.thread_count if latest.system_metrics else 0
                st.plotly_chart(create_gauge(thread_value, 'Thread Count', max_val=50), use_container_width=True)
            
            # Crypto Prices
            crypto_col1, crypto_col2 = st.columns(2)
            
            with crypto_col1:
                st.metric(
                    "Bitcoin Price (USD)",
                    f"${latest.crypto_metrics.bitcoin_price_usd:,.2f}" if (latest.crypto_metrics and latest.crypto_metrics.bitcoin_price_usd) else "N/A"
                )
            
            with crypto_col2:
                st.metric(
                    "Ethereum Price (USD)",
                    f"${latest.crypto_metrics.ethereum_price_usd:,.2f}" if (latest.crypto_metrics and latest.crypto_metrics.ethereum_price_usd) else "N/A"
                )
    
    except Exception as e:
        st.error(f"Error fetching live metrics: {str(e)}")
    
    # Historical Data Section
    st.header("Historical Data")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        options=['Last 24 Hours', 'Last Week'],
        index=0
    )
    
    try:
        # Calculate time range
        end_time = datetime.now(UTC)
        if time_range == 'Last 24 Hours':
            start_time = end_time - timedelta(days=1)
        else:  # Last Week
            start_time = end_time - timedelta(days=7)
        
        # Get historical metrics
        metrics = client.get_metrics(start_time=start_time, end_time=end_time, limit=1000)
        
        if metrics:
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': m.timestamp,
                'ram_usage': m.system_metrics.ram_usage_percent if m.system_metrics else None,
                'thread_count': m.system_metrics.thread_count if m.system_metrics else None,
                'bitcoin_price': m.crypto_metrics.bitcoin_price_usd if m.crypto_metrics else None,
                'ethereum_price': m.crypto_metrics.ethereum_price_usd if m.crypto_metrics else None
            } for m in metrics])
            
            # System Metrics Chart
            system_fig = go.Figure()
            system_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ram_usage'],
                                          name='RAM Usage %', mode='lines+markers'))
            system_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['thread_count'],
                                          name='Thread Count', mode='lines+markers',
                                          yaxis='y2'))
            
            system_fig.update_layout(
                title='System Metrics Over Time',
                yaxis={'title': 'RAM Usage %'},
                yaxis2={'title': 'Thread Count', 'overlaying': 'y', 'side': 'right'},
                hovermode='x unified'
            )
            
            st.plotly_chart(system_fig, use_container_width=True)
            
            # Crypto Prices Chart
            crypto_fig = go.Figure()
            crypto_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bitcoin_price'],
                                          name='Bitcoin', mode='lines+markers'))
            crypto_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ethereum_price'],
                                          name='Ethereum', mode='lines+markers'))
            
            crypto_fig.update_layout(
                title='Cryptocurrency Prices Over Time',
                yaxis={'title': 'Price (USD)'},
                hovermode='x unified'
            )
            
            st.plotly_chart(crypto_fig, use_container_width=True)
            
            # Data Table
            st.dataframe(
                df.assign(
                    timestamp=df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                    ram_usage=df['ram_usage'].round(2),
                    bitcoin_price=df['bitcoin_price'].round(2),
                    ethereum_price=df['ethereum_price'].round(2)
                )
            )
        
        else:
            st.info("No historical data available")
            
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")

if __name__ == "__main__":
    main()
    # Auto-refresh every 5 seconds
    time.sleep(5)
    st.rerun() 