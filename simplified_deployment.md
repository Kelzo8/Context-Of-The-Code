# Simplified Deployment: Local API + PythonAnywhere Dashboard

This guide explains how to run the API locally while deploying only the dashboard to PythonAnywhere.

## Step 1: Local API Setup

1. Run the API locally on your machine:
   ```bash
   python src/api.py
   ```
   
2. Make note of your local IP address (if you want other devices on your network to access it)
   - On Windows: Run `ipconfig` in Command Prompt
   - On Mac/Linux: Run `ifconfig` or `ip addr` in Terminal

3. The API will be available at `http://localhost:5000` or `http://YOUR_LOCAL_IP:5000`

## Step 2: Minimal PythonAnywhere Deployment

You only need to upload and configure these essential files:

1. `src/dashboard.py` - The main dashboard application
2. `requirements.txt` - Dependencies
3. `src/models.py` - Database models (if needed by the dashboard)
4. `src/metrics_sdk/` - The metrics SDK directory

## Step 3: Configure PythonAnywhere

1. Go to the "Web" tab and create a new web app
2. Choose "Manual configuration" and Python 3.10
3. Set up a WSGI file with this content:
   ```python
   import sys
   import os
   
   # Add the application directory to the Python path
   path = '/home/Kelzo/metrics-dashboard/src'
   if path not in sys.path:
       sys.path.append(path)
   
   # Import the dashboard application
   from dashboard import app as application
   ```

4. Set the environment variable:
   - `API_URL`: Set to `http://YOUR_LOCAL_IP:5000` (replace with your actual local IP)

## Step 4: Configure Port Forwarding (Optional)

If you want to access your local API from outside your network:

1. Set up port forwarding on your router to forward port 5000 to your local machine
2. Use a dynamic DNS service to get a stable domain name for your home IP
3. Update the `API_URL` environment variable to use this public address

## Step 5: Security Considerations

1. The API will be accessible to anyone who can reach your local machine
2. Consider adding authentication to your API
3. Use HTTPS if exposing your API to the internet

## Step 6: Testing

1. Start your local API
2. Visit your PythonAnywhere dashboard at https://Kelzo.pythonanywhere.com
3. Verify that the dashboard can connect to your local API

## Troubleshooting

- If the dashboard can't connect to your API, check:
  1. Your firewall settings (allow port 5000)
  2. The `API_URL` environment variable is correct
  3. Your local API is running
  4. PythonAnywhere's whitelist (you may need to upgrade to a paid account to access non-whitelisted domains) 