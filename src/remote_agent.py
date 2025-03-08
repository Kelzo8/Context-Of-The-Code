import psutil
import requests
import logging
import json
import os
import time
import socket
from datetime import datetime
import sqlite3
import argparse
from pathlib import Path

# Configure logging
def setup_logging(log_file='logs/remote_agent.log'):
    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up logger
    logger = logging.getLogger('RemoteAgent')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_system_metrics():
    """Collect system metrics from the local machine"""
    return {
        'thread_count': len(psutil.Process().threads()),
        'ram_usage_percent': psutil.virtual_memory().percent,
        'cpu_usage_percent': psutil.cpu_percent(interval=1),
        'disk_usage_percent': psutil.disk_usage('/').percent
    }

def get_crypto_prices():
    """Fetch cryptocurrency prices from CoinGecko API"""
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

class CloudMetricsUploader:
    """Uploads metrics to a cloud API or database"""
    
    def __init__(self, api_url=None, device_name=None, offline_db_path='metrics.db'):
        self.api_url = api_url
        self.device_name = device_name or socket.gethostname()
        self.offline_db_path = offline_db_path
        self.logger = logging.getLogger('RemoteAgent.Uploader')
        
        # Initialize local SQLite database for offline storage
        self._init_local_db()
    
    def _init_local_db(self):
        """Initialize the local SQLite database for offline storage"""
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            timestamp TEXT,
            metrics_json TEXT,
            uploaded INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_metrics(self, metrics_data):
        """Store metrics in the local database"""
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat()
        metrics_json = json.dumps(metrics_data)
        
        cursor.execute(
            "INSERT INTO metrics (device_name, timestamp, metrics_json, uploaded) VALUES (?, ?, ?, ?)",
            (self.device_name, timestamp, metrics_json, 0)
        )
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Stored metrics in local database: {timestamp}")
        
        # Try to upload any pending metrics
        self.upload_pending_metrics()
    
    def upload_pending_metrics(self):
        """Upload any pending metrics to the cloud API"""
        if not self.api_url:
            self.logger.warning("No API URL configured, skipping upload")
            return
        
        conn = sqlite3.connect(self.offline_db_path)
        cursor = conn.cursor()
        
        # Get all unuploaded metrics
        cursor.execute("SELECT id, device_name, timestamp, metrics_json FROM metrics WHERE uploaded = 0")
        pending_metrics = cursor.fetchall()
        
        if not pending_metrics:
            conn.close()
            return
        
        self.logger.info(f"Attempting to upload {len(pending_metrics)} pending metrics")
        
        for metric_id, device_name, timestamp, metrics_json in pending_metrics:
            try:
                metrics_data = json.loads(metrics_json)
                
                # Prepare payload for API
                payload = {
                    'device_name': device_name,
                    'timestamp': timestamp,
                    'metrics': metrics_data
                }
                
                # Send to API
                response = requests.post(f"{self.api_url}/v1/metrics", json=payload)
                
                if response.status_code in (200, 201):
                    # Mark as uploaded
                    cursor.execute("UPDATE metrics SET uploaded = 1 WHERE id = ?", (metric_id,))
                    conn.commit()
                    self.logger.info(f"Successfully uploaded metric ID {metric_id}")
                else:
                    self.logger.warning(f"Failed to upload metric ID {metric_id}: {response.status_code}")
            
            except Exception as e:
                self.logger.error(f"Error uploading metric ID {metric_id}: {str(e)}")
        
        conn.close()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Remote Metrics Agent')
    parser.add_argument('--api-url', help='URL of the metrics API')
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds')
    parser.add_argument('--db-path', default='metrics.db', help='Path to the local SQLite database')
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    logger.info(f"Starting Remote Metrics Agent on {socket.gethostname()}")
    
    # Initialize uploader
    uploader = CloudMetricsUploader(
        api_url=args.api_url,
        offline_db_path=args.db_path
    )
    
    # Main collection loop
    while True:
        try:
            # Collect metrics
            system_metrics = get_system_metrics()
            crypto_metrics = get_crypto_prices()
            
            # Combine metrics
            metrics_data = {
                'system': system_metrics,
                'crypto': crypto_metrics,
                'collection_time': datetime.utcnow().isoformat()
            }
            
            # Store and try to upload
            uploader.store_metrics(metrics_data)
            
            logger.info(f"Collected metrics: RAM {system_metrics['ram_usage_percent']}%, "
                       f"Threads {system_metrics['thread_count']}, "
                       f"CPU {system_metrics['cpu_usage_percent']}%, "
                       f"Disk {system_metrics['disk_usage_percent']}%")
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {str(e)}")
        
        # Wait for next collection
        time.sleep(args.interval)

if __name__ == "__main__":
    main() 