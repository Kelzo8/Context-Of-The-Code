import sys
import os

# Add the application directory to the Python path
path = '/home/Kelzo/metrics-dashboard/src'
if path not in sys.path:
    sys.path.append(path)

# For the dashboard (Dash application)
from dashboard import app as application

# If you want to deploy the API instead, comment out the line above and uncomment this:
# from api import app as application 