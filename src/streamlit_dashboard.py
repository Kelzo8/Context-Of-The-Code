import streamlit as st
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, UTC
import time
import os
import psutil
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

def get_system_metrics():
    """Get actual system metrics using psutil"""
    try:
        # Get RAM info
        ram_info = psutil.virtual_memory()
        
        # Get process and thread information
        process_threads = {}
        total_threads = 0
        python_threads = 0
        
        # Get current process
        current_process = psutil.Process()
        python_name = current_process.name()
        
        for proc in psutil.process_iter(['name', 'num_threads']):
            try:
                # Count threads for this process
                num_threads = proc.info['num_threads']
                total_threads += num_threads
                
                # Group by process name
                proc_name = proc.info['name']
                if proc_name in process_threads:
                    process_threads[proc_name] += num_threads
                else:
                    process_threads[proc_name] = num_threads
                    
                # Count Python-related threads
                if proc_name == python_name:
                    python_threads += num_threads
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort processes by thread count
        top_processes = dict(sorted(process_threads.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:5])
        
        return {
            'ram_usage_percent': ram_info.percent,
            'total_ram': ram_info.total,
            'used_ram': ram_info.used,
            'available_ram': ram_info.available,
            'thread_count': python_threads,  # Now showing only Python-related threads
            'total_threads': total_threads,
            'top_processes': top_processes
        }
    except Exception as e:
        st.error(f"Error getting system metrics: {str(e)}")
        return {
            'ram_usage_percent': 0,
            'total_ram': 0,
            'used_ram': 0,
            'available_ram': 0,
            'thread_count': 0,
            'total_threads': 0,
            'top_processes': {}
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
                btc_price = None
                eth_price = None
        except Exception as e:
            st.error(f"Error fetching crypto prices: {str(e)}")
            btc_price = None
            eth_price = None
        
        # System Metrics Row
        st.subheader("System Metrics")
        # Create three columns for system metrics
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.plotly_chart(
                create_gauge(metrics['ram_usage_percent'], 'RAM Usage %'),
                use_container_width=True
            )
            
        with m2:
            st.plotly_chart(
                create_gauge(metrics['thread_count'], 'Python Threads', max_val=100),
                use_container_width=True
            )
            
        with m3:
            # Display additional RAM info
            st.metric(
                "Total RAM",
                f"{metrics['total_ram'] / (1024**3):.1f} GB"
            )
            st.metric(
                "Available RAM",
                f"{metrics['available_ram'] / (1024**3):.1f} GB"
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
            
        # Display thread information
        st.subheader("Thread Information")
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.metric("Total System Threads", metrics['total_threads'])
            st.metric("Python Process Threads", metrics['thread_count'])
            
        with col_info2:
            st.markdown("**Top Processes by Thread Count:**")
            for proc_name, thread_count in metrics['top_processes'].items():
                st.text(f"{proc_name}: {thread_count} threads")
        
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
                    name='RAM Usage %'
                ))
                fig_system.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['thread_count'],
                    name='Thread Count',
                    yaxis='y2'
                ))
                fig_system.update_layout(
                    title='System Metrics Over Time',
                    yaxis=dict(title='RAM Usage %'),
                    yaxis2=dict(title='Thread Count', overlaying='y', side='right')
                )
                st.plotly_chart(fig_system, use_container_width=True)
                
                # Crypto Prices Chart
                fig_crypto = go.Figure()
                fig_crypto.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['bitcoin_price'],
                    name='Bitcoin'
                ))
                fig_crypto.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['ethereum_price'],
                    name='Ethereum'
                ))
                fig_crypto.update_layout(
                    title='Cryptocurrency Prices Over Time',
                    yaxis=dict(title='Price (USD)')
                )
                st.plotly_chart(fig_crypto, use_container_width=True)
                
                # Data Table
                st.dataframe(
                    df.assign(
                        timestamp=df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                        ram_usage=df['ram_usage'].round(2),
                        bitcoin_price=df['bitcoin_price'].round(2),
                        ethereum_price=df['ethereum_price'].round(2)
                    ).sort_values('timestamp', ascending=False)
                )
            else:
                st.warning("No historical data available")
        except Exception as e:
            st.error(f"Error loading historical data: {str(e)}")
    
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
                    
                    if 'error' in result:
                        st.error(f"Failed to restart app: {result['error']}")
                    else:
                        st.success("Restart command sent successfully!")
                        st.json(result)
                except Exception as e:
                    st.error(f"Error sending restart command: {str(e)}")
        
        # Command History (placeholder for future implementation)
        st.subheader("Command History")
        st.info("Command history will be available in a future update")

# Auto-refresh the dashboard
if __name__ == "__main__":
    main()
    # Rerun the app every 5 seconds
    time.sleep(5)
    st.rerun() 