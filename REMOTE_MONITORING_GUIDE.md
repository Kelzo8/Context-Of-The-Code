# Remote System Monitoring Guide

This guide explains how to set up remote system monitoring between your local PC and Streamlit Cloud.

## Overview

The solution consists of two main components:

1. **Remote Agent**: Runs on your local PC, collects system metrics, and sends them to the cloud
2. **Cloud API/Dashboard**: Runs on Streamlit Cloud, receives metrics from your PC and displays them

This approach allows you to monitor your local PC's metrics (RAM, CPU, threads, etc.) from anywhere using Streamlit Cloud.

## Setup Instructions

### Step 1: Deploy the Cloud API on Streamlit Cloud

1. Fork or clone this repository to your GitHub account
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository and the `src/cloud_api.py` file as the main file
5. Deploy the app
6. Note the URL of your deployed app (e.g., `https://your-metrics-dashboard.streamlit.app`)

### Step 2: Set Up the Remote Agent on Your PC

1. Make sure you have Python installed on your PC
2. Clone this repository to your PC:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the remote agent, pointing it to your Streamlit Cloud app:
   ```bash
   python src/remote_agent.py --api-url https://your-metrics-dashboard.streamlit.app
   ```

   Replace `https://your-metrics-dashboard.streamlit.app` with the actual URL of your deployed Streamlit app.

5. (Optional) Set up the agent to run automatically at startup:

   **Windows:**
   
   Create a batch file (e.g., `start_agent.bat`) with the following content:
   ```batch
   @echo off
   cd C:\path\to\your\repository
   python src\remote_agent.py --api-url https://your-metrics-dashboard.streamlit.app
   ```
   
   Then add this batch file to your startup folder:
   1. Press `Win+R`, type `shell:startup`, and press Enter
   2. Copy or create a shortcut to your batch file in this folder

   **macOS:**
   
   Create a launch agent by creating a file at `~/Library/LaunchAgents/com.yourusername.metricsagent.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.yourusername.metricsagent</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/path/to/your/repository/src/remote_agent.py</string>
           <string>--api-url</string>
           <string>https://your-metrics-dashboard.streamlit.app</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
   </dict>
   </plist>
   ```
   
   Then load the agent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.yourusername.metricsagent.plist
   ```

   **Linux:**
   
   Create a systemd service by creating a file at `/etc/systemd/system/metrics-agent.service`:
   ```
   [Unit]
   Description=System Metrics Remote Agent
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your/repository/src/remote_agent.py --api-url https://your-metrics-dashboard.streamlit.app
   WorkingDirectory=/path/to/your/repository
   Restart=always
   User=yourusername

   [Install]
   WantedBy=multi-user.target
   ```
   
   Then enable and start the service:
   ```bash
   sudo systemctl enable metrics-agent
   sudo systemctl start metrics-agent
   ```

### Step 3: View Your Metrics

1. Open your Streamlit Cloud app in a web browser
2. You should see your PC's metrics displayed in the dashboard
3. The metrics will update automatically as new data is sent from your PC

## Troubleshooting

### Agent Can't Connect to the Cloud API

1. Check that your Streamlit Cloud app is running
2. Verify the API URL is correct
3. Check your internet connection
4. Look for error messages in the agent's log file (`logs/remote_agent.log`)

### No Data Showing in the Dashboard

1. Check that the remote agent is running on your PC
2. Verify that metrics are being collected (check the log file)
3. The agent stores metrics locally if it can't connect to the cloud, and will upload them when the connection is restored

### Agent Crashes or Stops Working

1. Check the log file for error messages
2. Make sure your PC has an internet connection
3. Restart the agent

## Advanced Configuration

### Changing the Collection Interval

By default, the agent collects metrics every 60 seconds. You can change this with the `--interval` parameter:

```bash
python src/remote_agent.py --api-url https://your-metrics-dashboard.streamlit.app --interval 30
```

### Using a Different Database Path

By default, the agent stores metrics in `metrics.db` in the current directory. You can change this with the `--db-path` parameter:

```bash
python src/remote_agent.py --api-url https://your-metrics-dashboard.streamlit.app --db-path /path/to/your/database.db
```

## Security Considerations

- The communication between the agent and the cloud API is not encrypted by default
- The Streamlit Cloud app is publicly accessible
- Consider implementing authentication if your metrics are sensitive

## Extending the Solution

You can extend this solution to:

1. Monitor multiple PCs by running the agent on each one
2. Add more metrics (network usage, GPU stats, etc.)
3. Set up alerts for when metrics exceed certain thresholds
4. Add authentication to the cloud API 