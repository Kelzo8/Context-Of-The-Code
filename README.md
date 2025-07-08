# System & Crypto Metrics Dashboard

A real-time dashboard built with Streamlit that monitors system metrics and cryptocurrency prices. The dashboard pulls data from a custom API and updates automatically.

## Features

### Live Metrics
- **System Monitoring**
  - RAM Usage % with real-time gauge visualization
  - System Thread Count with dynamic gauge display
  - Auto-refreshing metrics (configurable refresh rate)

- **Cryptocurrency Tracking**
  - Live Bitcoin (BTC) price in USD
  - Live Ethereum (ETH) price in USD
  - Real-time price updates

### Historical Data
- Customizable time range views:
  - Last 24 Hours
  - Last Week
- Interactive charts showing:
  - System metrics over time
  - Cryptocurrency price trends
- Detailed data table with historical records

### Device Management
- Multi-device support
- Remote app restart functionality
- Force restart option for unresponsive applications

### Dashboard Settings
- Configurable refresh rate (1-60 seconds)
- API connection status monitoring
- Development mode with API URL configuration

## Setup

1. Install required packages:
```bash
pip install streamlit plotly pandas psutil python-dotenv wmi
```

2. Set up environment variables:
Create a `.env` file with:
```
API_URL=your_api_url_here
STREAMLIT_ENV=development  # Optional for development mode
```

3. Run the dashboard:
```bash
streamlit run streamlit_app.py
```

## Deployment

The dashboard is deployed on Streamlit Cloud and can be accessed at:
https://context-of-the-code.streamlit.app/

## API Integration

The dashboard integrates with a custom API that provides:
- System metrics (RAM usage, thread count)
- Cryptocurrency prices
- Historical data
- Used Grok for hosting api

## Features in Detail

### Auto-Refresh
- Dashboard automatically updates based on the selected refresh rate
- No manual refresh required
- Configurable through the sidebar slider

### System Metrics
- RAM Usage: Shows percentage of used RAM
- Thread Count: Displays current system threads
- Both metrics update in real-time

### Cryptocurrency Data
- Real-time price updates for BTC and ETH
- Historical price tracking
- Interactive price charts

### Data Visualization
- Dynamic gauges for system metrics
- Interactive time series charts
- Sortable historical data table

## Contributing

Feel free to submit issues and enhancement requests!
