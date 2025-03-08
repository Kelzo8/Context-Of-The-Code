# System Metrics Dashboard

A dashboard application for monitoring system metrics and cryptocurrency prices.

## Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```
   python src/init_db.py
   ```

3. Run the metrics collector:
   ```
   python src/metrics_collector.py
   ```

4. Run the API server:
   ```
   python src/api.py
   ```

5. Run the Streamlit dashboard:
   ```
   streamlit run src/streamlit_dashboard.py
   ```

## Deployment on Streamlit Cloud

1. Push your code to a GitHub repository
2. Visit [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository, branch, and the main file path (src/streamlit_dashboard.py)
6. Click "Deploy"

The application will be automatically deployed and accessible via a public URL.

## Configuration

The application uses the following configuration files:
- `.streamlit/config.toml`: Contains theme and server settings
- `requirements.txt`: Lists Python package dependencies
- `packages.txt`: Lists system dependencies

## Dependencies

- Python 3.7+
- Streamlit
- Plotly
- Pandas
- SQLAlchemy
- Other dependencies as listed in requirements.txt

## Remote Monitoring Setup

To monitor your local PC from Streamlit Cloud:

1. Install ngrok:
   ```
   # Windows (using chocolatey)
   choco install ngrok

   # macOS
   brew install ngrok

   # Linux
   snap install ngrok
   ```

2. Sign up at [ngrok.com](https://ngrok.com/) and get your auth token

3. Configure ngrok:
   ```
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. Start your local API server:
   ```
   python src/api.py
   ```

5. Create a tunnel to your API:
   ```
   ngrok http 5000
   ```

6. Copy the HTTPS URL provided by ngrok (e.g., https://abc123.ngrok.io)

7. Update your Streamlit Cloud settings with this URL:
   - Go to your app on Streamlit Cloud
   - Click on "Manage app" > "Settings" > "Secrets"
   - Add a new secret: `API_URL` with the ngrok URL value

8. Restart your Streamlit app