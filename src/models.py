import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship with snapshots
    snapshots = relationship('Snapshot', back_populates='device')

class Snapshot(Base):
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # Relationships
    device = relationship('Device', back_populates='snapshots')
    system_metrics = relationship('SystemMetric', back_populates='snapshot', uselist=False)
    crypto_metrics = relationship('CryptoMetric', back_populates='snapshot', uselist=False)

class SystemMetric(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    thread_count = Column(Integer)
    ram_usage_percent = Column(Float)
    
    # Relationship with snapshot
    snapshot = relationship('Snapshot', back_populates='system_metrics')

class CryptoMetric(Base):
    __tablename__ = 'crypto_metrics'
    
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'))
    bitcoin_price_usd = Column(Float)
    ethereum_price_usd = Column(Float)
    
    # Relationship with snapshot
    snapshot = relationship('Snapshot', back_populates='crypto_metrics')

def get_database_engine(db_path=None):
    """Get database engine based on environment"""
    if db_path is None:
        # Check for environment variable (for cloud deployment)
        db_path = os.getenv('DATABASE_URL', 'metrics.db')
    
    # Handle SQLite path for PythonAnywhere
    if not db_path.startswith('sqlite:///'):
        db_path = f'sqlite:///{db_path}'
    
    return create_engine(db_path, echo=False)  # Set echo to False in production 