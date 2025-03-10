import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
import tempfile
import shutil
import json
from pathlib import Path
import requests
import logging

from .client import MetricsClient
from .models import SystemMetrics, CryptoMetrics, MetricsSnapshot

# Disable logging during tests
logging.getLogger('MetricsSDK').setLevel(logging.CRITICAL)

class TestMetricsSDK(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = MetricsClient(
            base_url='http://localhost:5000',
            device_id=1,
            offline_storage_path=self.temp_dir
        )
        
    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir)
        
    def test_metrics_models(self):
        """Test the metrics data models."""
        # Test SystemMetrics
        sys_metrics = SystemMetrics(thread_count=10, ram_usage_percent=75.5)
        self.assertEqual(sys_metrics.thread_count, 10)
        self.assertEqual(sys_metrics.ram_usage_percent, 75.5)
        
        # Test CryptoMetrics
        crypto_metrics = CryptoMetrics(bitcoin_price_usd=50000.0, ethereum_price_usd=3000.0)
        self.assertEqual(crypto_metrics.bitcoin_price_usd, 50000.0)
        self.assertEqual(crypto_metrics.ethereum_price_usd, 3000.0)
        
        # Test MetricsSnapshot
        snapshot = MetricsSnapshot(
            device_id=1,
            timestamp=datetime.now(UTC),
            system_metrics=sys_metrics,
            crypto_metrics=crypto_metrics
        )
        self.assertEqual(snapshot.device_id, 1)
        self.assertIsNotNone(snapshot.timestamp)
        
    def test_metrics_serialization(self):
        """Test serialization and deserialization of metrics."""
        original = MetricsSnapshot(
            device_id=1,
            timestamp=datetime.now(UTC),
            system_metrics=SystemMetrics(thread_count=10, ram_usage_percent=75.5),
            crypto_metrics=CryptoMetrics(bitcoin_price_usd=50000.0, ethereum_price_usd=3000.0)
        )
        
        # Test serialization
        data = original.to_dict()
        self.assertIsInstance(data, dict)
        
        # Test deserialization
        restored = MetricsSnapshot.from_dict(data)
        self.assertEqual(restored.device_id, original.device_id)
        self.assertEqual(restored.system_metrics.thread_count, original.system_metrics.thread_count)
        self.assertEqual(restored.crypto_metrics.bitcoin_price_usd, original.crypto_metrics.bitcoin_price_usd)
        
    @patch('requests.post')
    def test_post_metrics_success(self, mock_post):
        """Test successful metrics upload."""
        # Mock successful response
        mock_post.return_value = MagicMock(status_code=201)
        
        success = self.client.post_metrics(
            system_metrics=SystemMetrics(thread_count=10, ram_usage_percent=75.5),
            crypto_metrics=CryptoMetrics(bitcoin_price_usd=50000.0, ethereum_price_usd=3000.0)
        )
        
        self.assertTrue(success)
        self.assertTrue(mock_post.called)
        
    @patch('requests.post')
    def test_post_metrics_offline_storage(self, mock_post):
        """Test offline storage when upload fails."""
        # Mock failed response
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        success = self.client.post_metrics(
            system_metrics=SystemMetrics(thread_count=10, ram_usage_percent=75.5)
        )
        
        # Should still return True as metrics are stored offline
        self.assertTrue(success)
        
        # Check if file was stored
        stored_files = list(Path(self.temp_dir).glob("metrics_*.json"))
        self.assertEqual(len(stored_files), 1)
        
        # Verify stored data
        with open(stored_files[0], 'r') as f:
            stored_data = json.load(f)
            self.assertEqual(stored_data['system_metrics']['thread_count'], 10)
        
    @patch('requests.get')
    def test_get_metrics(self, mock_get):
        """Test metrics retrieval."""
        # Mock successful response
        mock_response = {
            'snapshot_id': 1,
            'device_id': 1,
            'timestamp': datetime.now(UTC).isoformat(),
            'system_metrics': {
                'thread_count': 10,
                'ram_usage_percent': 75.5
            }
        }
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [mock_response]
        )
        
        metrics = self.client.get_metrics(limit=1)
        
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].system_metrics.thread_count, 10)
        self.assertTrue(mock_get.called)
        
    @patch('requests.get')
    def test_get_metrics_error(self, mock_get):
        """Test metrics retrieval error handling."""
        # Mock failed response
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        metrics = self.client.get_metrics()
        
        self.assertEqual(len(metrics), 0)
        self.assertTrue(mock_get.called)

if __name__ == '__main__':
    unittest.main() 