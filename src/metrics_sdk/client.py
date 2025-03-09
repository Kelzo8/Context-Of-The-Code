import os
import json
import time
from datetime import datetime, UTC
from typing import List, Optional
import requests
from pathlib import Path
import logging
from .models import MetricsSnapshot, SystemMetrics, CryptoMetrics

class MetricsClient:
    """Client for interacting with the Metrics API."""
    
    def __init__(self, base_url: str, device_id: int, 
                 offline_storage_path: str = "offline_metrics",
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the metrics client.
        
        Args:
            base_url: Base URL of the metrics API
            device_id: ID of the device sending metrics
            offline_storage_path: Path to store metrics when offline
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.device_id = device_id
        self.offline_storage_path = Path(offline_storage_path)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create offline storage directory
        self.offline_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('MetricsSDK')
        self.logger.setLevel(logging.INFO)
        
        # Try to upload any stored offline metrics
        self._upload_stored_metrics()
    
    def _store_offline(self, snapshot: MetricsSnapshot) -> None:
        """Store metrics offline for later upload."""
        timestamp = snapshot.timestamp.strftime('%Y%m%d_%H%M%S_%f')
        filepath = self.offline_storage_path / f"metrics_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(snapshot.to_dict(), f)
        
        self.logger.info(f"Stored metrics offline: {filepath}")
    
    def _upload_stored_metrics(self) -> None:
        """Try to upload any stored offline metrics."""
        if not self.offline_storage_path.exists():
            return
            
        for filepath in self.offline_storage_path.glob("metrics_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                snapshot = MetricsSnapshot.from_dict(data)
                success = self._upload_with_retry(snapshot)
                
                if success:
                    os.remove(filepath)
                    self.logger.info(f"Successfully uploaded and removed stored metrics: {filepath}")
                    
            except Exception as e:
                self.logger.error(f"Error processing stored metrics {filepath}: {str(e)}")
    
    def _upload_with_retry(self, snapshot: MetricsSnapshot) -> bool:
        """Upload metrics with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/v1/metrics",
                    json=snapshot.to_dict()
                )
                
                if response.status_code == 201:
                    return True
                    
                if response.status_code == 400:  # Bad request, don't retry
                    self.logger.error(f"Bad request: {response.json().get('error')}")
                    return False
                    
            except requests.RequestException as e:
                self.logger.warning(f"Upload attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        return False
    
    def post_metrics(self, 
                    system_metrics: Optional[SystemMetrics] = None,
                    crypto_metrics: Optional[CryptoMetrics] = None) -> bool:
        """
        Upload metrics to the API.
        
        Returns:
            bool: True if upload was successful (immediately or stored for later)
        """
        snapshot = MetricsSnapshot(
            device_id=self.device_id,
            timestamp=datetime.now(UTC),
            system_metrics=system_metrics,
            crypto_metrics=crypto_metrics
        )
        
        # Try to upload immediately
        success = self._upload_with_retry(snapshot)
        
        # If upload failed, store offline
        if not success:
            self._store_offline(snapshot)
            
        return True
    
    def get_metrics(self, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[MetricsSnapshot]:
        """
        Get metrics from the API.
        
        Args:
            start_time: Start time for filtering metrics
            end_time: End time for filtering metrics
            limit: Maximum number of metrics to return
            
        Returns:
            List of MetricsSnapshot objects
        """
        params = {'limit': limit}
        
        if start_time:
            params['start_time'] = start_time.isoformat()
        if end_time:
            params['end_time'] = end_time.isoformat()
            
        try:
            response = requests.get(f"{self.base_url}/v1/metrics", params=params)
            response.raise_for_status()
            
            data = response.json()
            return [MetricsSnapshot.from_dict(item) for item in data]
        except Exception as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return []
            
    def send_command(self, command_type: str, params: Optional[dict] = None) -> dict:
        """
        Send a command to the device.
        
        Args:
            command_type: Type of command to send (e.g., 'restart_app', 'reboot')
            params: Additional parameters for the command
            
        Returns:
            Response from the API as a dictionary
        """
        if params is None:
            params = {}
            
        payload = {
            'command_type': command_type,
            'params': params
        }
        
        try:
            # Add debug logging
            self.logger.info(f"Sending command to {self.base_url}/v1/devices/{self.device_id}/commands")
            self.logger.info(f"Payload: {payload}")
            
            response = requests.post(
                f"{self.base_url}/v1/devices/{self.device_id}/commands", 
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Add debug logging for response
            self.logger.info(f"Response status code: {response.status_code}")
            self.logger.info(f"Response content: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending command: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
            
    def restart_app(self, app_name: str, force: bool = False) -> dict:
        """
        Restart a specific application on the device.
        
        Args:
            app_name: Name of the application to restart
            force: Whether to force restart the application
            
        Returns:
            Response from the API as a dictionary
        """
        return self.send_command('restart_app', {
            'app_name': app_name,
            'force': force
        }) 