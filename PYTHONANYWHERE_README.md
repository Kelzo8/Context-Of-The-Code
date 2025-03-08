# PythonAnywhere Deployment

This README provides a quick reference for deploying this application to PythonAnywhere.

## Quick Start

1. **Upload Files**: Upload all project files to `/home/Kelzo/metrics-dashboard/`
2. **Install Dependencies**: 
   ```
   cd ~/metrics-dashboard
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Initialize Database**:
   ```
   python pythonanywhere_init_db.py
   ```
4. **Configure Web App**:
   - Go to Web tab
   - Set source code directory: `/home/Kelzo/metrics-dashboard`
   - Set WSGI file to use content from `pythonanywhere_wsgi.py`
   - Set environment variables:
     - `API_URL`: `https://Kelzo.pythonanywhere.com`
     - `DATABASE_URL`: `sqlite:////home/Kelzo/metrics-dashboard/metrics.db`

5. **Reload Web App**:
   - Click "Reload" button in Web tab

## Troubleshooting

If you encounter issues:
1. Check error logs in Web tab
2. Ensure all paths are correct for your PythonAnywhere username
3. Verify virtual environment is activated when running commands

For more detailed instructions, see `pythonanywhere_setup.md` 