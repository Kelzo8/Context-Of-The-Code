import psutil
import requests
import logging
import json
from datetime import datetime
import time
import socket
from sqlalchemy.orm import sessionmaker
from models import get_database_engine, Device, Snapshot, SystemMetric, CryptoMetric

# Configure logging
def setup_logging():
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up file handler
    file_handler = logging.FileHandler('logs/metrics.log')
    file_handler.setFormatter(formatter)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up logger
    logger = logging.getLogger('MetricsCollector')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

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
        return {
            'bitcoin_price_usd': None,
            'ethereum_price_usd': None
        }

def main():
    logger = setup_logging()
    
    # Set up database connection
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get or create device
    hostname = socket.gethostname()
    device = session.query(Device).filter_by(name=hostname).first()
    
    if not device:
        logger.error(f"Device {hostname} not found in database. Please run init_db.py first.")
        return
    
    while True:
        try:
            # Collect metrics
            system_metrics_data = get_system_metrics()
            crypto_prices_data = get_crypto_prices()
            
            # Create new snapshot
            snapshot = Snapshot(
                device=device,
                timestamp=datetime.utcnow()
            )
            
            # Create system metrics
            system_metrics = SystemMetric(
                snapshot=snapshot,
                **system_metrics_data
            )
            
            # Create crypto metrics
            crypto_metrics = CryptoMetric(
                snapshot=snapshot,
                **crypto_prices_data
            )
            
            # Add to session and commit
            session.add(snapshot)
            session.add(system_metrics)
            session.add(crypto_metrics)
            session.commit()
            
            # Create metrics payload for logging
            metrics = {
                'timestamp': snapshot.timestamp.isoformat(),
                'system': system_metrics_data,
                **crypto_prices_data
            }
            
            # Log metrics
            logger.info(f"Collected and stored metrics: {json.dumps(metrics, indent=2)}")
            
            # Wait for 60 seconds before next collection
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            session.rollback()
            time.sleep(60)

if __name__ == "__main__":
    main() 