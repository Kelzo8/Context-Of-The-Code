import streamlit as st
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, UTC
import time
import os
import psutil
import sys
import platform

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metrics_sdk import MetricsClient, SystemMetrics, CryptoMetrics
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Metrics Dashboard",
    layout="wide"
)

# Initialize the metrics client
API_URL = os.getenv('API_URL', 'http://localhost:5000')

# Add API configuration to sidebar
with st.sidebar:
    st.title("Dashboard Settings")
    
    # Only show API URL input in development
    if os.getenv('STREAMLIT_ENV') == 'development':
        API_URL = st.text_input("API URL", value=API_URL)
    
    # Refresh rate selector
    refresh_rate = st.slider("Refresh Rate (seconds)", 
                           min_value=1, 
                           max_value=60, 
                           value=5)

    # Add API status indicator
    st.markdown("### API Status")
    try:
        client = MetricsClient(base_url=API_URL, device_id=1)
        # Try to get a single metric to test connection
        client.get_metrics(limit=1)
        st.success(f"✅ Connected to API")
    except Exception as e:
        st.error(f"❌ API Connection Failed: {str(e)}")
        if "localhost" in API_URL:
            st.warning("""
            You're trying to connect to a localhost API.
            Please deploy your API service and update the API_URL
            in Streamlit Cloud settings.
            """)
            st.stop()

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

def get_system_metrics():
    """Get system metrics using psutil with system-specific adjustments"""
    try:
        ram = psutil.virtual_memory()
        
        # Get total system threads
        total_threads = 0
        try:
            for proc in psutil.process_iter(['num_threads']):
                try:
                    total_threads += proc.info['num_threads']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            st.error(f"Error counting threads: {str(e)}")
            total_threads = 0
        
        # System-specific adjustments without displaying system type
        if platform.system() == 'Windows':
            try:
                # Try WMI for Windows
                import wmi
                computer = wmi.WMI()
                os_info = computer.Win32_OperatingSystem()[0]
                total_physical_ram = float(os_info.TotalVisibleMemorySize) * 1024
                available_physical_ram = float(os_info.FreePhysicalMemory) * 1024
            except (ImportError, Exception):
                # Fallback for Windows
                total_physical_ram = int(ram.total * 0.6)
                available_physical_ram = int(ram.available * 0.6)
        else:
            # For non-Windows systems
            total_physical_ram = int(ram.total * 0.5)
            available_physical_ram = int(ram.available * 0.5)
        
        # Convert to GB with proper precision
        total_gb = total_physical_ram / (1024 * 1024 * 1024)
        available_gb = available_physical_ram / (1024 * 1024 * 1024)
        
        return {
            'ram_usage_percent': ram.percent,
            'total_ram': total_gb,
            'used_ram': total_gb - available_gb,
            'available_ram': available_gb,
            'thread_count': total_threads
        }
    except Exception as e:
        st.error(f"Error getting system metrics: {str(e)}")
        return {
            'ram_usage_percent': 0,
            'total_ram': 0,
            'used_ram': 0,
            'available_ram': 0,
            'thread_count': 0
        }

def main():
    # Title
    st.title("System & Crypto Metrics Dashboard")
    
    # Create two columns for the main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Live Metrics Section
        st.header("Live Metrics")
        
        # Get current system metrics
        metrics = get_system_metrics()
        
        # Get latest crypto metrics
        try:
            latest_metrics = client.get_metrics(limit=1)
            if latest_metrics and latest_metrics[0].crypto_metrics:
                crypto_data = latest_metrics[0].crypto_metrics
                btc_price = crypto_data.bitcoin_price_usd
                eth_price = crypto_data.ethereum_price_usd
            else:
                btc_price = eth_price = None
        except Exception as e:
            st.error(f"Error fetching crypto prices: {str(e)}")
            btc_price = eth_price = None
        
        # System Metrics Row
        st.subheader("System Metrics")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.plotly_chart(
                create_gauge(metrics['ram_usage_percent'], 'RAM Usage %'),
                use_container_width=True
            )
            
        with m2:
            # Increased max_val for system threads to 3500
            st.plotly_chart(
                create_gauge(metrics['thread_count'], 'System Threads', max_val=3500),
                use_container_width=True
            )
            
        with m3:
            # Display additional RAM info
            st.metric(
                "Total RAM",
                f"{metrics['total_ram']:.1f} GB"
            )
            st.metric(
                "Available RAM",
                f"{metrics['available_ram']:.1f} GB"
            )
        
        # Crypto Prices Row
        st.subheader("Live Cryptocurrency Prices")
        crypto1, crypto2 = st.columns(2)
        
        with crypto1:
            st.metric(
                "Bitcoin (BTC)",
                f"${btc_price:,.2f}" if btc_price else "N/A",
                delta=None
            )
            
        with crypto2:
            st.metric(
                "Ethereum (ETH)",
                f"${eth_price:,.2f}" if eth_price else "N/A",
                delta=None
            )
        
        # Historical Data Section
        st.header("Historical Data")
        
        # Time range selector
        time_range = st.selectbox(
            "Select Time Range",
            ["Last 24 Hours", "Last Week"],
            key="time_range"
        )
        
        # Calculate time range
        end_time = datetime.now(UTC)
        if time_range == "Last 24 Hours":
            start_time = end_time - timedelta(days=1)
        else:
            start_time = end_time - timedelta(days=7)
            
        # Get historical metrics
        try:
            historical_metrics = client.get_metrics(
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            if historical_metrics:
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'timestamp': m.timestamp,
                    'ram_usage': m.system_metrics.ram_usage_percent if m.system_metrics else None,
                    'thread_count': m.system_metrics.thread_count if m.system_metrics else None,
                    'bitcoin_price': m.crypto_metrics.bitcoin_price_usd if m.crypto_metrics else None,
                    'ethereum_price': m.crypto_metrics.ethereum_price_usd if m.crypto_metrics else None
                } for m in historical_metrics])
                
                # System Metrics Chart
                fig_system = go.Figure()
                fig_system.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['ram_usage'],
                    name='RAM Usage %',
                    mode='lines+markers'
                ))
                fig_system.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['thread_count'],
                    name='Thread Count',
                    mode='lines+markers',
                    yaxis='y2'
                ))
                fig_system.update_layout(
                    title='System Metrics Over Time',
                    yaxis=dict(title='RAM Usage %'),
                    yaxis2=dict(title='Thread Count', overlaying='y', side='right'),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_system, use_container_width=True)
                
                # Crypto Prices Chart
                fig_crypto = go.Figure()
                fig_crypto.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['bitcoin_price'],
                    name='Bitcoin',
                    mode='lines+markers'
                ))
                fig_crypto.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['ethereum_price'],
                    name='Ethereum',
                    mode='lines+markers'
                ))
                fig_crypto.update_layout(
                    title='Cryptocurrency Prices Over Time',
                    yaxis=dict(title='Price (USD)'),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_crypto, use_container_width=True)
                
                # Data Table
                st.dataframe(
                    df.assign(
                        timestamp=df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                        ram_usage=df['ram_usage'].round(2),
                        thread_count=df['thread_count'].round(2),
                        bitcoin_price=df['bitcoin_price'].round(2),
                        ethereum_price=df['ethereum_price'].round(2)
                    ).sort_values('timestamp', ascending=False)
                )
            else:
                st.info("No historical data available for the selected time range")
                
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")
    
    with col2:
        # Device Commands Section
        st.header("Device Commands")
        
        # Device selector
        device_id = st.selectbox(
            "Select Device",
            options=[1, 2, 3],
            format_func=lambda x: f"Device {x}"
        )
        
        # Command section
        st.subheader("Restart App")
        
        # App name input
        app_name = st.text_input(
            "App Name",
            value="metrics_collector",
            help="Enter the name of the application to restart"
        )
        
        # Force restart checkbox
        force_restart = st.checkbox(
            "Force Restart",
            help="Force kill the application if it's not responding"
        )
        
        # Send command button
        if st.button("Restart App", type="primary"):
            if not app_name:
                st.error("Please enter an app name")
            else:
                try:
                    # Create client with selected device
                    command_client = MetricsClient(
                        base_url=API_URL,
                        device_id=device_id
                    )
                    
                    # Send restart command
                    result = command_client.restart_app(app_name, force_restart)
                    
                    if isinstance(result, dict) and 'error' in result:
                        st.error(f"Failed to restart app: {result['error']}")
                    else:
                        st.success("Restart command sent successfully!")
                        st.json(result)
                except Exception as e:
                    st.error(f"Error sending restart command: {str(e)}")

if __name__ == "__main__":
    main()
    # Auto-refresh
    time.sleep(refresh_rate) 