import os
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, UTC
import time
from metrics_sdk import MetricsClient, SystemMetrics, CryptoMetrics

# Initialize the metrics client with environment variable
API_URL = os.getenv('API_URL', 'http://localhost:5000')
client = MetricsClient(
    base_url=API_URL,
    device_id=1
)

# Initialize the Dash app
app = dash.Dash(__name__, title='Metrics Dashboard')
server = app.server  # This is important for production deployment

# Layout
app.layout = html.Div([
    # Header
    html.H1('System & Crypto Metrics Dashboard', style={'textAlign': 'center'}),
    
    # Live Metrics Section
    html.Div([
        html.H2('Live Metrics'),
        html.Div([
            # System Metrics Gauges
            html.Div([
                dcc.Graph(id='ram-gauge'),
                dcc.Graph(id='thread-gauge'),
            ], style={'display': 'flex', 'justifyContent': 'space-around'}),
            
            # Crypto Prices Cards
            html.Div([
                html.Div([
                    html.H3('Bitcoin Price (USD)'),
                    html.H4(id='bitcoin-price')
                ], className='crypto-card'),
                html.Div([
                    html.H3('Ethereum Price (USD)'),
                    html.H4(id='ethereum-price')
                ], className='crypto-card'),
            ], style={'display': 'flex', 'justifyContent': 'space-around'})
        ])
    ]),
    
    # Device Commands Section
    html.Div([
        html.H2('Restart App'),
        html.Div([
            # Device Selection
            html.Div([
                html.Label('Select Device:'),
                dcc.Dropdown(
                    id='device-selector',
                    options=[
                        {'label': 'Device 1', 'value': 1},
                        {'label': 'Device 2', 'value': 2},
                        {'label': 'Device 3', 'value': 3}
                    ],
                    value=1
                ),
            ], style={'width': '200px', 'margin': '10px'}),
            
            # App Name Input
            html.Div([
                html.Label('App Name:'),
                dcc.Input(
                    id='app-name-input',
                    type='text',
                    placeholder='Enter app name',
                    value='metrics_collector',
                    style={'width': '100%'}
                ),
            ], style={'width': '200px', 'margin': '10px'}),
            
            # Force Restart Checkbox
            html.Div([
                dcc.Checklist(
                    id='force-restart',
                    options=[
                        {'label': 'Force Restart', 'value': 'force'}
                    ],
                    value=[]
                ),
            ], style={'margin': '10px'}),
            
            # Restart Button
            html.Button('Restart App', id='restart-app-button', n_clicks=0, 
                       style={'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 
                              'padding': '10px 20px', 'borderRadius': '5px', 'margin': '10px'}),
            
            # Command Status
            html.Div(id='command-status', style={'margin': '10px', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
        ], style={'display': 'flex', 'flexDirection': 'column'})
    ]),
    
    # Historical Data Section
    html.Div([
        html.H2('Historical Data'),
        
        # Filters
        html.Div([
            html.Label('Time Range:'),
            dcc.Dropdown(
                id='time-range',
                options=[
                    {'label': 'Last 24 Hours', 'value': '24H'},
                    {'label': 'Last Week', 'value': '7D'}
                ],
                value='24H'
            )
        ], style={'width': '200px', 'margin': '10px'}),
        
        # Charts
        dcc.Graph(id='system-metrics-chart'),
        dcc.Graph(id='crypto-prices-chart'),
        
        # Data Table
        html.Div([
            dash_table.DataTable(
                id='metrics-table',
                columns=[
                    {'name': 'Timestamp', 'id': 'timestamp'},
                    {'name': 'RAM Usage (%)', 'id': 'ram_usage'},
                    {'name': 'Thread Count', 'id': 'thread_count'},
                    {'name': 'Bitcoin Price', 'id': 'bitcoin_price'},
                    {'name': 'Ethereum Price', 'id': 'ethereum_price'}
                ],
                page_size=10,
                style_table={'overflowX': 'auto'},
                sort_action='native',
                filter_action='native'
            )
        ])
    ]),
    
    # Hidden div for storing data
    html.Div(id='metrics-store', style={'display': 'none'}),
    
    # Interval component for updates
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Update every 5 seconds
        n_intervals=0
    )
])

def create_gauge(value, title, min_val=0, max_val=100):
    """Create a gauge chart"""
    return {
        'data': [{
            'type': 'indicator',
            'mode': 'gauge+number',
            'value': value,
            'title': {'text': title},
            'gauge': {
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': 'darkblue'},
                'steps': [
                    {'range': [0, max_val*0.6], 'color': 'lightgray'},
                    {'range': [max_val*0.6, max_val*0.8], 'color': 'gray'},
                    {'range': [max_val*0.8, max_val], 'color': 'darkgray'}
                ]
            }
        }],
        'layout': {'height': 250}
    }

def create_empty_chart(title):
    """Create an empty chart with a message"""
    return {
        'data': [],
        'layout': {
            'title': title,
            'annotations': [{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20}
            }]
        }
    }

@app.callback(
    [Output('ram-gauge', 'figure'),
     Output('thread-gauge', 'figure'),
     Output('bitcoin-price', 'children'),
     Output('ethereum-price', 'children'),
     Output('metrics-store', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_live_metrics(n):
    """Update live metrics"""
    try:
        # Get latest metrics
        metrics = client.get_metrics(limit=1)
        
        if not metrics:
            return (
                create_gauge(0, 'RAM Usage %'),
                create_gauge(0, 'Thread Count', max_val=50),
                'N/A',
                'N/A',
                '[]'
            )
        
        latest = metrics[0]
        
        # Update gauges
        ram_gauge = create_gauge(
            latest.system_metrics.ram_usage_percent if latest.system_metrics else 0,
            'RAM Usage %'
        )
        
        thread_gauge = create_gauge(
            latest.system_metrics.thread_count if latest.system_metrics else 0,
            'Thread Count',
            max_val=50
        )
        
        # Update crypto prices
        btc_price = f"${latest.crypto_metrics.bitcoin_price_usd:,.2f}" if (latest.crypto_metrics and latest.crypto_metrics.bitcoin_price_usd) else "N/A"
        eth_price = f"${latest.crypto_metrics.ethereum_price_usd:,.2f}" if (latest.crypto_metrics and latest.crypto_metrics.ethereum_price_usd) else "N/A"
        
        # Store the latest data
        store_data = pd.DataFrame([{
            'timestamp': latest.timestamp,
            'ram_usage': latest.system_metrics.ram_usage_percent if latest.system_metrics else None,
            'thread_count': latest.system_metrics.thread_count if latest.system_metrics else None,
            'bitcoin_price': latest.crypto_metrics.bitcoin_price_usd if latest.crypto_metrics else None,
            'ethereum_price': latest.crypto_metrics.ethereum_price_usd if latest.crypto_metrics else None
        }]).to_json()
        
        return ram_gauge, thread_gauge, btc_price, eth_price, store_data
        
    except Exception as e:
        print(f"Error in update_live_metrics: {str(e)}")
        return dash.no_update

@app.callback(
    [Output('system-metrics-chart', 'figure'),
     Output('crypto-prices-chart', 'figure'),
     Output('metrics-table', 'data')],
    [Input('time-range', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_historical_data(time_range, n):
    """Update historical data visualizations"""
    try:
        # Calculate time range
        end_time = datetime.now(UTC)
        if time_range == '24H':
            start_time = end_time - timedelta(days=1)
        else:  # '7D'
            start_time = end_time - timedelta(days=7)
        
        # Get historical metrics
        metrics = client.get_metrics(start_time=start_time, end_time=end_time, limit=1000)
        
        # Handle no data case
        if not metrics:
            return (
                create_empty_chart('System Metrics Over Time'),
                create_empty_chart('Cryptocurrency Prices Over Time'),
                []
            )
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': m.timestamp,
            'ram_usage': m.system_metrics.ram_usage_percent if m.system_metrics else None,
            'thread_count': m.system_metrics.thread_count if m.system_metrics else None,
            'bitcoin_price': m.crypto_metrics.bitcoin_price_usd if m.crypto_metrics else None,
            'ethereum_price': m.crypto_metrics.ethereum_price_usd if m.crypto_metrics else None
        } for m in metrics])
        
        # Handle empty DataFrame
        if df.empty:
            return (
                create_empty_chart('System Metrics Over Time'),
                create_empty_chart('Cryptocurrency Prices Over Time'),
                []
            )
        
        # Create system metrics chart
        system_fig = {
            'data': [
                go.Scatter(x=df['timestamp'], y=df['ram_usage'], name='RAM Usage %',
                          mode='lines+markers'),
                go.Scatter(x=df['timestamp'], y=df['thread_count'], name='Thread Count',
                          yaxis='y2', mode='lines+markers')
            ],
            'layout': {
                'title': 'System Metrics Over Time',
                'yaxis': {'title': 'RAM Usage %'},
                'yaxis2': {'title': 'Thread Count', 'overlaying': 'y', 'side': 'right'},
                'hovermode': 'x unified'
            }
        }
        
        # Create crypto prices chart
        crypto_fig = {
            'data': [
                go.Scatter(x=df['timestamp'], y=df['bitcoin_price'], name='Bitcoin',
                          mode='lines+markers'),
                go.Scatter(x=df['timestamp'], y=df['ethereum_price'], name='Ethereum',
                          mode='lines+markers')
            ],
            'layout': {
                'title': 'Cryptocurrency Prices Over Time',
                'yaxis': {'title': 'Price (USD)'},
                'hovermode': 'x unified'
            }
        }
        
        # Format table data
        table_data = df.assign(
            timestamp=df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
            ram_usage=df['ram_usage'].round(2),
            bitcoin_price=df['bitcoin_price'].round(2),
            ethereum_price=df['ethereum_price'].round(2)
        ).to_dict('records')
        
        return system_fig, crypto_fig, table_data
        
    except Exception as e:
        print(f"Error in update_historical_data: {str(e)}")
        return (
            create_empty_chart('System Metrics Over Time'),
            create_empty_chart('Cryptocurrency Prices Over Time'),
            []
        )

# Callback for sending commands to devices
@app.callback(
    Output('command-status', 'children'),
    [Input('restart-app-button', 'n_clicks')],
    [State('device-selector', 'value'),
     State('app-name-input', 'value'),
     State('force-restart', 'value')]
)
def send_device_command(n_clicks, device_id, app_name, force_restart):
    # Don't trigger on initial load
    if n_clicks == 0:
        return html.Div("Ready to restart app", style={'color': 'gray'})
    
    # Validate inputs
    if not app_name or app_name.strip() == '':
        return html.Div("Error: App name cannot be empty", style={'color': 'red'})
    
    # Create a new client with the selected device ID
    command_client = MetricsClient(
        base_url=API_URL,
        device_id=device_id
    )
    
    try:
        # Use the specific restart_app method
        force = 'force' in force_restart
        print(f"Sending restart command for app '{app_name}' to device {device_id} (force={force})")
        
        result = command_client.restart_app(app_name, force)
        
        if 'error' in result:
            error_msg = result['error']
            print(f"Error from API: {error_msg}")
            return html.Div([
                html.P("Failed to restart app", style={'color': 'red', 'fontWeight': 'bold'}),
                html.P(f"Error: {error_msg}", style={'color': 'red'})
            ])
        else:
            return html.Div([
                html.P(f"Restart command sent successfully!", style={'color': 'green', 'fontWeight': 'bold'}),
                html.P(f"App: {app_name}", style={'marginBottom': '5px'}),
                html.P(f"Force restart: {'Yes' if force else 'No'}", style={'marginBottom': '5px'}),
                html.P(f"Status: {result.get('status', 'unknown')}", style={'marginBottom': '5px'}),
                html.P(f"Command ID: {result.get('command_id', 'unknown')}", style={'marginBottom': '5px'}),
                html.P(f"Timestamp: {result.get('timestamp', 'unknown')}", style={'marginBottom': '5px'})
            ])
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error sending restart command: {str(e)}")
        print(error_details)
        
        return html.Div([
            html.P("Failed to restart app", style={'color': 'red', 'fontWeight': 'bold'}),
            html.P(f"Error: {str(e)}", style={'color': 'red'}),
            html.Details([
                html.Summary("Technical Details"),
                html.Pre(error_details, style={'whiteSpace': 'pre-wrap', 'fontSize': '12px'})
            ])
        ])

# Add CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .crypto-card {
                padding: 20px;
                margin: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                background-color: white;
                flex: 1;
                text-align: center;
            }
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .dash-table-container {
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050) 