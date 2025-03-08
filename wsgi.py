import sys
import os

# Add the directory containing your app to Python path
path = '/home/YOUR_USERNAME/metrics-dashboard'
if path not in sys.path:
    sys.path.append(path)

# Import your Flask application
from dashboard import app as application

# Run the Streamlit app
def application(environ, start_response):
    bootstrap.run(main, '', [], )
    return [''] 