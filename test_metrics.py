from models import Base, Device, Snapshot, SystemMetric, CryptoMetric, get_database_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

def test_database_connection():
    """Test database connection and initialization"""
    print("\n1. Testing Database Connection...")
    try:
        engine = get_database_engine('test_metrics.db')
        Base.metadata.create_all(engine)
        print("✓ Database connection successful")
        return engine
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None

def test_data_insertion(engine):
    """Test inserting sample data"""
    print("\n2. Testing Data Insertion...")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test device
        test_device = Device(
            name='test_device',
            device_type='test'
        )
        session.add(test_device)
        session.commit()
        
        # Create test snapshot with metrics
        test_snapshot = Snapshot(
            device=test_device,
            timestamp=datetime.utcnow()
        )
        
        test_system_metrics = SystemMetric(
            snapshot=test_snapshot,
            thread_count=10,
            ram_usage_percent=45.5
        )
        
        test_crypto_metrics = CryptoMetric(
            snapshot=test_snapshot,
            bitcoin_price_usd=50000.0,
            ethereum_price_usd=3000.0
        )
        
        session.add(test_snapshot)
        session.add(test_system_metrics)
        session.add(test_crypto_metrics)
        session.commit()
        
        print("✓ Test data inserted successfully")
        return test_device.id
    except Exception as e:
        print(f"✗ Data insertion failed: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def test_data_query(engine, device_id):
    """Test querying stored data"""
    print("\n3. Testing Data Queries...")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query device and its latest snapshot
        device = session.query(Device).filter_by(id=device_id).first()
        if not device:
            print("✗ Test device not found")
            return
        
        print(f"\nDevice Information:")
        print(f"Name: {device.name}")
        print(f"Type: {device.device_type}")
        print(f"Created: {device.created_at}")
        
        # Get latest snapshot with metrics
        latest_snapshot = (
            session.query(Snapshot)
            .filter_by(device_id=device_id)
            .order_by(Snapshot.timestamp.desc())
            .first()
        )
        
        if latest_snapshot:
            print(f"\nLatest Snapshot ({latest_snapshot.timestamp}):")
            
            system_metrics = latest_snapshot.system_metrics
            print("\nSystem Metrics:")
            print(f"Thread Count: {system_metrics.thread_count}")
            print(f"RAM Usage: {system_metrics.ram_usage_percent}%")
            
            crypto_metrics = latest_snapshot.crypto_metrics
            print("\nCrypto Metrics:")
            print(f"Bitcoin Price: ${crypto_metrics.bitcoin_price_usd}")
            print(f"Ethereum Price: ${crypto_metrics.ethereum_price_usd}")
            
            print("\n✓ Data query successful")
        else:
            print("✗ No snapshots found")
            
    except Exception as e:
        print(f"✗ Data query failed: {e}")
    finally:
        session.close()

def main():
    print("=== Testing Metrics Collection System ===")
    
    # Test database connection
    engine = test_database_connection()
    if not engine:
        return
    
    # Test data insertion
    device_id = test_data_insertion(engine)
    if not device_id:
        return
    
    # Test data query
    test_data_query(engine, device_id)
    
    print("\n=== Test Complete ===")
    print("\nNext steps:")
    print("1. Run the actual metrics collector:")
    print("   python src/metrics_collector.py")
    print("2. Check the logs in logs/metrics.log")
    print("3. Query the database using the provided functions")

if __name__ == "__main__":
    main() 