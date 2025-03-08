import streamlit as st
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, UTC
import time
import psutil
import requests
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Database setup
Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    snapshots = relationship('Snapshot', back_populates='device')

class Snapshot(Base):
    __tablename__ = 'snapshots'
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    device = relationship('Device', back_populates='snapshots')
    system_metrics = relationship('SystemMetric', back_populates='snapshot', uselist=False)
    crypto_metrics = relationship('CryptoMetric', back_populates='snapshot', uselist=False)

class SystemMetric(Base):
    __tablename__ = 'system_metrics'
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    thread_count = Column(Integer)
    ram_usage_percent = Column(Float)
    snapshot = relationship('Snapshot', back_populates='system_metrics')

class CryptoMetric(Base):
    __tablename__ = 'crypto_metrics'
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    bitcoin_price_usd = Column(Float)
    ethereum_price_usd = Column(Float)
    snapshot = relationship('Snapshot', back_populates='crypto_metrics')

# Initialize database
@st.cache_resource
def init_db():
    db_path = 'sqlite:///metrics.db'
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    return engine

# Get database session
def get_db_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

# Data collection functions
def get_system_metrics():
    return {
        'thread_count': len(psutil.Process().threads()),
        'ram_usage_percent': psutil.virtual_memory().percent
    }

def get_crypto_prices():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd')
        data = response.json()
        return {
            'bitcoin_price_usd': data['bitcoin']['usd'],
            'ethereum_price_usd': data['ethereum']['usd']
        }
    except Exception as e:
        st.error(f"Failed to fetch crypto prices: {str(e)}")
        return {'bitcoin_price_usd': None, 'ethereum_price_usd': None}

def collect_metrics(session, device_id=1):
    # Create new snapshot
    snapshot = Snapshot(device_id=device_id)
    session.add(snapshot)
    
    # Add system metrics
    sys_metrics = get_system_metrics()
    system_metrics = SystemMetric(
        snapshot=snapshot,
        thread_count=sys_metrics['thread_count'],
        ram_usage_percent=sys_metrics['ram_usage_percent']
    )
    session.add(system_metrics)
    
    # Add crypto metrics
    crypto_prices = get_crypto_prices()
    crypto_metrics = CryptoMetric(
        snapshot=snapshot,
        bitcoin_price_usd=crypto_prices['bitcoin_price_usd'],
        ethereum_price_usd=crypto_prices['ethereum_price_usd']
    )
    session.add(crypto_metrics)
    
    session.commit()
    return snapshot

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
    # Page config
    st.set_page_config(
        page_title="Metrics Dashboard",
        layout="wide"
    )
    
    # Title
    st.title("System & Crypto Metrics Dashboard")
    
    # Initialize session state for auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Initialize database and create default device if needed
    session = get_db_session()
    device = session.query(Device).filter_by(id=1).first()
    if not device:
        device = Device(id=1, name='Default Device', device_type='System')
        session.add(device)
        session.commit()
    
    # Collect new metrics every 5 seconds
    if (datetime.now() - st.session_state.last_refresh).total_seconds() >= 5:
        collect_metrics(session)
        st.session_state.last_refresh = datetime.now()
    
    # Live Metrics Section
    st.header("Live Metrics")
    col1, col2 = st.columns(2)
    
    try:
        # Get latest metrics
        latest = session.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
        
        if latest:
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
        snapshots = session.query(Snapshot).filter(
            Snapshot.timestamp.between(start_time, end_time)
        ).order_by(Snapshot.timestamp.desc()).limit(1000).all()
        
        if snapshots:
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': s.timestamp,
                'ram_usage': s.system_metrics.ram_usage_percent if s.system_metrics else None,
                'thread_count': s.system_metrics.thread_count if s.system_metrics else None,
                'bitcoin_price': s.crypto_metrics.bitcoin_price_usd if s.crypto_metrics else None,
                'ethereum_price': s.crypto_metrics.ethereum_price_usd if s.crypto_metrics else None
            } for s in snapshots])
            
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
    
    finally:
        session.close()

if __name__ == "__main__":
    main() 