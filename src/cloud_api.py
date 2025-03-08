import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import pandas as pd
from pathlib import Path

# Initialize database
def init_db():
    """Initialize the SQLite database"""
    db_path = "metrics.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        created_at TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        timestamp TEXT,
        system_metrics TEXT,
        crypto_metrics TEXT,
        FOREIGN KEY (device_id) REFERENCES devices (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    return db_path

# Get or create device
def get_or_create_device(device_name):
    """Get or create a device by name"""
    conn = sqlite3.connect("metrics.db")
    cursor = conn.cursor()
    
    # Check if device exists
    cursor.execute("SELECT id FROM devices WHERE name = ?", (device_name,))
    device = cursor.fetchone()
    
    if device:
        device_id = device[0]
    else:
        # Create new device
        cursor.execute(
            "INSERT INTO devices (name, created_at) VALUES (?, ?)",
            (device_name, datetime.utcnow().isoformat())
        )
        conn.commit()
        device_id = cursor.lastrowid
    
    conn.close()
    return device_id

# Store metrics
def store_metrics(device_id, timestamp, metrics):
    """Store metrics in the database"""
    conn = sqlite3.connect("metrics.db")
    cursor = conn.cursor()
    
    system_metrics = json.dumps(metrics.get('system', {}))
    crypto_metrics = json.dumps(metrics.get('crypto', {}))
    
    cursor.execute(
        "INSERT INTO metrics (device_id, timestamp, system_metrics, crypto_metrics) VALUES (?, ?, ?, ?)",
        (device_id, timestamp, system_metrics, crypto_metrics)
    )
    
    conn.commit()
    conn.close()

# Get metrics
def get_metrics(device_id=None, limit=100):
    """Get metrics from the database"""
    conn = sqlite3.connect("metrics.db")
    cursor = conn.cursor()
    
    query = """
    SELECT d.name, m.timestamp, m.system_metrics, m.crypto_metrics
    FROM metrics m
    JOIN devices d ON m.device_id = d.id
    """
    
    params = []
    if device_id:
        query += " WHERE m.device_id = ?"
        params.append(device_id)
    
    query += " ORDER BY m.timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        device_name, timestamp, system_metrics, crypto_metrics = row
        result.append({
            'device_name': device_name,
            'timestamp': timestamp,
            'system': json.loads(system_metrics),
            'crypto': json.loads(crypto_metrics)
        })
    
    conn.close()
    return result

# API endpoints
def api_receive_metrics():
    """API endpoint to receive metrics from remote agents"""
    try:
        # Get JSON data from request
        data = st.session_state.get('_metrics_data', {})
        
        if not data:
            return {"error": "No data provided"}, 400
        
        device_name = data.get('device_name')
        timestamp = data.get('timestamp')
        metrics = data.get('metrics')
        
        if not all([device_name, timestamp, metrics]):
            return {"error": "Missing required fields"}, 400
        
        # Get or create device
        device_id = get_or_create_device(device_name)
        
        # Store metrics
        store_metrics(device_id, timestamp, metrics)
        
        return {"status": "success"}, 201
    
    except Exception as e:
        return {"error": str(e)}, 500

def api_get_metrics():
    """API endpoint to get metrics"""
    try:
        # Get query parameters
        params = st.session_state.get('_metrics_params', {})
        device_name = params.get('device_name')
        limit = int(params.get('limit', 100))
        
        # Get device ID if name provided
        device_id = None
        if device_name:
            conn = sqlite3.connect("metrics.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM devices WHERE name = ?", (device_name,))
            device = cursor.fetchone()
            conn.close()
            
            if device:
                device_id = device[0]
            else:
                return {"error": f"Device not found: {device_name}"}, 404
        
        # Get metrics
        metrics = get_metrics(device_id, limit)
        
        return metrics, 200
    
    except Exception as e:
        return {"error": str(e)}, 500

# Streamlit app
def main():
    st.set_page_config(page_title="Metrics Cloud API", layout="wide")
    
    # Initialize database
    init_db()
    
    # Sidebar
    st.sidebar.title("Metrics Cloud API")
    st.sidebar.info("""
    This application serves as both a REST API for receiving metrics from remote agents
    and a dashboard for viewing those metrics.
    """)
    
    # API documentation
    with st.expander("API Documentation", expanded=False):
        st.markdown("""
        ## API Endpoints
        
        ### POST /api/metrics
        
        Receive metrics from a remote agent.
        
        **Request Body:**
        ```json
        {
            "device_name": "my-pc",
            "timestamp": "2023-01-01T12:00:00Z",
            "metrics": {
                "system": {
                    "ram_usage_percent": 75.5,
                    "thread_count": 120,
                    "cpu_usage_percent": 25.3,
                    "disk_usage_percent": 68.2
                },
                "crypto": {
                    "bitcoin_price_usd": 45000.0,
                    "ethereum_price_usd": 3000.0
                }
            }
        }
        ```
        
        ### GET /api/metrics
        
        Get metrics from the database.
        
        **Query Parameters:**
        - `device_name`: Filter by device name
        - `limit`: Maximum number of results (default: 100)
        """)
    
    # Main content
    st.title("System Metrics Dashboard")
    
    # Get metrics
    metrics = get_metrics(limit=1000)
    
    if not metrics:
        st.info("No metrics data available. Connect a remote agent to start collecting data.")
        return
    
    # Convert to DataFrame
    df_list = []
    for m in metrics:
        system = m['system']
        crypto = m['crypto']
        
        df_list.append({
            'device': m['device_name'],
            'timestamp': datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')),
            'ram_usage': system.get('ram_usage_percent'),
            'thread_count': system.get('thread_count'),
            'cpu_usage': system.get('cpu_usage_percent'),
            'disk_usage': system.get('disk_usage_percent'),
            'bitcoin_price': crypto.get('bitcoin_price_usd'),
            'ethereum_price': crypto.get('ethereum_price_usd')
        })
    
    df = pd.DataFrame(df_list)
    
    # Device selector
    devices = df['device'].unique()
    selected_device = st.selectbox("Select Device", devices)
    
    # Filter by device
    df_device = df[df['device'] == selected_device]
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Latest System Metrics")
        latest = df_device.iloc[0]
        st.metric("RAM Usage", f"{latest['ram_usage']:.1f}%")
        st.metric("CPU Usage", f"{latest['cpu_usage']:.1f}%")
    
    with col2:
        st.subheader("Latest Thread Count")
        st.metric("Thread Count", f"{latest['thread_count']}")
        st.metric("Disk Usage", f"{latest['disk_usage']:.1f}%")
    
    # Charts
    st.subheader("System Metrics Over Time")
    
    # RAM and CPU usage chart
    ram_cpu_chart = {
        'data': [
            {
                'x': df_device['timestamp'],
                'y': df_device['ram_usage'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'RAM Usage %'
            },
            {
                'x': df_device['timestamp'],
                'y': df_device['cpu_usage'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'CPU Usage %'
            }
        ],
        'layout': {
            'title': 'RAM and CPU Usage',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Usage %'}
        }
    }
    st.plotly_chart(ram_cpu_chart, use_container_width=True)
    
    # Thread count chart
    thread_chart = {
        'data': [
            {
                'x': df_device['timestamp'],
                'y': df_device['thread_count'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Thread Count'
            }
        ],
        'layout': {
            'title': 'Thread Count',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Count'}
        }
    }
    st.plotly_chart(thread_chart, use_container_width=True)
    
    # Data table
    st.subheader("Raw Data")
    st.dataframe(df_device.sort_values('timestamp', ascending=False))

# Handle API requests
def handle_api_request():
    # Check if this is an API request
    path = st.experimental_get_query_params().get('_path', [''])[0]
    
    if path == '/api/metrics':
        method = st.experimental_get_query_params().get('_method', ['GET'])[0]
        
        if method == 'POST':
            # Handle POST request
            st.session_state['_metrics_data'] = json.loads(st.experimental_get_query_params().get('_body', ['{}'])[0])
            result, status_code = api_receive_metrics()
            st.json(result)
            st.stop()
        
        elif method == 'GET':
            # Handle GET request
            st.session_state['_metrics_params'] = st.experimental_get_query_params()
            result, status_code = api_get_metrics()
            st.json(result)
            st.stop()

if __name__ == "__main__":
    # Check for API requests
    try:
        handle_api_request()
    except:
        pass
    
    # Run the Streamlit app
    main() 