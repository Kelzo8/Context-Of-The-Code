from flask import Flask, request, jsonify
from models import Device, Snapshot, SystemMetric, CryptoMetric, get_database_engine
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime
import socket

app = Flask(__name__)

# Initialize database connection
engine = get_database_engine()
Session = sessionmaker(bind=engine)

def get_db_session():
    """Get a new database session"""
    return Session()

@app.route('/v1/devices', methods=['POST'])
def register_device():
    """Register a new device"""
    session = get_db_session()
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('device_type'):
            return jsonify({
                'error': 'Missing required fields: name and device_type'
            }), 400
            
        # Check if device already exists
        existing_device = session.query(Device).filter_by(name=data['name']).first()
        if existing_device:
            return jsonify({
                'error': 'Device already registered',
                'device_id': existing_device.id
            }), 409
            
        # Create new device
        device = Device(
            name=data['name'],
            device_type=data['device_type']
        )
        session.add(device)
        session.commit()
        
        return jsonify({
            'message': 'Device registered successfully',
            'device_id': device.id
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/v1/metrics', methods=['POST'])
def upload_metrics():
    """Upload new metrics for a device"""
    session = get_db_session()
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('device_id'):
            return jsonify({'error': 'Missing device_id'}), 400
            
        # Check if device exists
        device = session.query(Device).get(data['device_id'])
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        # Create new snapshot with metrics
        snapshot = Snapshot(
            device_id=device.id,
            timestamp=datetime.utcnow()
        )
        
        # Add system metrics if provided
        if 'system_metrics' in data:
            system_metrics = SystemMetric(
                snapshot=snapshot,
                thread_count=data['system_metrics'].get('thread_count'),
                ram_usage_percent=data['system_metrics'].get('ram_usage_percent')
            )
            session.add(system_metrics)
            
        # Add crypto metrics if provided
        if 'crypto_metrics' in data:
            crypto_metrics = CryptoMetric(
                snapshot=snapshot,
                bitcoin_price_usd=data['crypto_metrics'].get('bitcoin_price_usd'),
                ethereum_price_usd=data['crypto_metrics'].get('ethereum_price_usd')
            )
            session.add(crypto_metrics)
            
        session.add(snapshot)
        session.commit()
        
        return jsonify({
            'message': 'Metrics uploaded successfully',
            'snapshot_id': snapshot.id
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/v1/metrics', methods=['GET'])
def get_metrics():
    """Retrieve metrics with filtering options"""
    session = get_db_session()
    try:
        # Get query parameters
        device_id = request.args.get('device_id')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = session.query(Snapshot)
        
        if device_id:
            query = query.filter(Snapshot.device_id == device_id)
        if start_time:
            query = query.filter(Snapshot.timestamp >= start_time)
        if end_time:
            query = query.filter(Snapshot.timestamp <= end_time)
            
        # Get results with related metrics
        snapshots = query.options(
            joinedload(Snapshot.system_metrics),
            joinedload(Snapshot.crypto_metrics)
        ).order_by(Snapshot.timestamp.desc()).limit(limit).all()
        
        # Format response
        results = []
        for snapshot in snapshots:
            result = {
                'snapshot_id': snapshot.id,
                'device_id': snapshot.device_id,
                'timestamp': snapshot.timestamp.isoformat(),
                'system_metrics': {
                    'thread_count': snapshot.system_metrics.thread_count,
                    'ram_usage_percent': snapshot.system_metrics.ram_usage_percent
                } if snapshot.system_metrics else None,
                'crypto_metrics': {
                    'bitcoin_price_usd': snapshot.crypto_metrics.bitcoin_price_usd,
                    'ethereum_price_usd': snapshot.crypto_metrics.ethereum_price_usd
                } if snapshot.crypto_metrics else None
            }
            results.append(result)
            
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/v1/snapshots', methods=['GET'])
def get_snapshots():
    """Retrieve snapshot summaries"""
    session = get_db_session()
    try:
        # Get query parameters
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = session.query(Snapshot).join(Device)
        
        if device_id:
            query = query.filter(Snapshot.device_id == device_id)
            
        # Get results
        snapshots = query.order_by(Snapshot.timestamp.desc()).limit(limit).all()
        
        # Format response
        results = []
        for snapshot in snapshots:
            result = {
                'snapshot_id': snapshot.id,
                'device_id': snapshot.device_id,
                'device_name': snapshot.device.name,
                'timestamp': snapshot.timestamp.isoformat(),
                'has_system_metrics': snapshot.system_metrics is not None,
                'has_crypto_metrics': snapshot.crypto_metrics is not None
            }
            results.append(result)
            
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 