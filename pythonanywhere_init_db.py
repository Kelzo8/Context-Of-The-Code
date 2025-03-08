import os
import sys

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Import the database initialization function
from init_db import initialize_database

if __name__ == '__main__':
    print("Initializing database...")
    initialize_database()
    print("Database initialization complete!") 