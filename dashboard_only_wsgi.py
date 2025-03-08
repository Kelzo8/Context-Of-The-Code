import sys
import os

# Add the application directory to the Python path
path = '/home/Kelzo/metrics-dashboard/src'
if path not in sys.path:
    sys.path.append(path)

# Import the dashboard application
from dashboard import app as application 