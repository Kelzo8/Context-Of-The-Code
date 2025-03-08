import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000/v1'

def test_register_device():
    """Test device registration endpoint"""
    print("\n1. Testing Device Registration...")
    
    # Test data
    device_data = {
        'name': 'test_api_device',
        'device_type': 'api_test'
    }
    
    # Make request
    response = requests.post(f'{BASE_URL}/devices', json=device_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get('device_id') if response.status_code in (201, 409) else None

def test_upload_metrics(device_id):
    """Test metrics upload endpoint"""
    print("\n2. Testing Metrics Upload...")
    
    # Test data
    metrics_data = {
        'device_id': device_id,
        'system_metrics': {
            'thread_count': 15,
            'ram_usage_percent': 55.5
        },
        'crypto_metrics': {
            'bitcoin_price_usd': 52000.0,
            'ethereum_price_usd': 3200.0
        }
    }
    
    # Make request
    response = requests.post(f'{BASE_URL}/metrics', json=metrics_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json().get('snapshot_id') if response.status_code == 201 else None

def test_get_metrics(device_id):
    """Test metrics retrieval endpoint"""
    print("\n3. Testing Metrics Retrieval...")
    
    # Make request with query parameters
    params = {
        'device_id': device_id,
        'limit': 5
    }
    response = requests.get(f'{BASE_URL}/metrics', params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_snapshots(device_id):
    """Test snapshots retrieval endpoint"""
    print("\n4. Testing Snapshots Retrieval...")
    
    # Make request with query parameters
    params = {
        'device_id': device_id,
        'limit': 5
    }
    response = requests.get(f'{BASE_URL}/snapshots', params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("=== Testing Metrics API ===")
    
    # Test device registration
    device_id = test_register_device()
    if not device_id:
        print("❌ Failed to get device ID. Stopping tests.")
        return
        
    # Test metrics upload
    snapshot_id = test_upload_metrics(device_id)
    if not snapshot_id:
        print("❌ Failed to upload metrics. Stopping tests.")
        return
        
    # Small delay to ensure data is stored
    import time
    time.sleep(1)
        
    # Test metrics retrieval
    test_get_metrics(device_id)
    
    # Test snapshots retrieval
    test_get_snapshots(device_id)
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    main() 