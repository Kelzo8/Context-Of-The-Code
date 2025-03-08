# Streamlit Dashboard Application

This is a Streamlit-based dashboard application that visualizes data using Plotly.

## Local Development

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
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