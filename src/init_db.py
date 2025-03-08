from models import Base, Device, get_database_engine
from sqlalchemy.orm import sessionmaker
import socket

def init_database():
    # Create database engine
    engine = get_database_engine()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session factory
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add current device if it doesn't exist
        hostname = socket.gethostname()
        device = session.query(Device).filter_by(name=hostname).first()
        
        if not device:
            device = Device(
                name=hostname,
                device_type='workstation'
            )
            session.add(device)
            session.commit()
            print(f"Added device: {hostname}")
        else:
            print(f"Device {hostname} already exists")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_database() 