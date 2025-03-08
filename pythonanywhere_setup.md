# Deploying to PythonAnywhere

This guide will help you deploy your metrics dashboard application to PythonAnywhere at https://Kelzo.pythonanywhere.com.

## Step 1: Set Up Your PythonAnywhere Account

1. Log in to your PythonAnywhere account at https://www.pythonanywhere.com/login/
2. If you haven't already, verify that your username is "Kelzo"

## Step 2: Upload Your Code

### Option 1: Using Git (Recommended)

1. Go to the "Consoles" tab and start a new Bash console
2. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_REPOSITORY_URL.git ~/metrics-dashboard
   ```
   (Replace YOUR_REPOSITORY_URL with your actual repository URL)

### Option 2: Manual Upload

1. Go to the "Files" tab
2. Create a new directory: `metrics-dashboard`
3. Navigate into the directory
4. Upload all your project files using the "Upload a file" button
   - Make sure to maintain the same directory structure

## Step 3: Set Up a Virtual Environment

1. In a Bash console, run:
   ```bash
   cd ~/metrics-dashboard
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Step 4: Configure Web App

1. Go to the "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10 (or the version compatible with your requirements)
5. Set the path to your project: `/home/Kelzo/metrics-dashboard`

## Step 5: Configure WSGI File

1. Click on the WSGI configuration file link (e.g., `/var/www/kelzo_pythonanywhere_com_wsgi.py`)
2. Replace the contents with:

```python
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
```

## Step 6: Configure Static Files (for Dash)

1. In the "Web" tab, scroll down to "Static files"
2. Add a new entry:
   - URL: `/assets`
   - Directory: `/home/Kelzo/metrics-dashboard/src/assets`

## Step 7: Set Environment Variables

1. In the "Web" tab, scroll down to "Environment variables"
2. Add the following variables:
   - `API_URL`: Set to `https://Kelzo.pythonanywhere.com` (for the dashboard to connect to the API)
   - `DATABASE_URL`: Set to `sqlite:////home/Kelzo/metrics-dashboard/metrics.db`

## Step 8: Initialize the Database

1. In a Bash console, run:
   ```bash
   cd ~/metrics-dashboard
   source venv/bin/activate
   python src/init_db.py
   ```

## Step 9: Reload the Web App

1. Go back to the "Web" tab
2. Click the "Reload" button

## Step 10: Check the Logs

1. If you encounter any issues, check the error logs in the "Web" tab
2. Click on the "Error log" link to view any errors

## Additional Notes

- PythonAnywhere free accounts only allow web apps to make external requests to whitelisted domains. If your app needs to access external APIs, you may need to whitelist those domains.
- If you need to run both the API and dashboard, you'll need a paid account to set up multiple web apps.
- For a free account, you can choose to deploy either the dashboard or the API, but not both simultaneously. 