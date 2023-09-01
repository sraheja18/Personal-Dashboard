import dash
from dash import dcc, html
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import smtplib
import os
import numpy as np
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from dash.dependencies import Input, Output

load_dotenv()

class EmailService:
    def __init__(self):
        self.address = os.environ.get("EMAIL_ADDRESS")
        self.password = os.environ.get("EMAIL_PASSWORD")
        
    def send(self, to_address, subject, message):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.address
        msg['To'] = to_address
        msg.set_content(message)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(self.address, self.password)
            smtp.send_message(msg)


def get_stock_data(ticker):
    """Fetch stock data for Microsoft and Tesla over 7 days"""
    stock_data = yf.download(ticker, period='7d')
    return stock_data['Close']

def get_meteo_data(lat = 47.6062, lon=122.3321):
    """get weather data from open meteo REST API"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&temperature_unit=fahrenheit&timezone=America%2FLos_Angeles"
        data = requests.get(url).json()
        meteo = pd.DataFrame(data["daily"])
        return meteo
    except Exception as e:
        print(str(e))
        return None

# Get weather data


app = dash.Dash(__name__)

box_style = {
    'width': '40%',
    'fontSize': '20px',
    'textAlign': 'center',
    'border': '1px solid #ddd',
    'padding': '20px',
    'backgroundColor': '#f9f9f9'
}

@app.callback([Output('subplot-graph','figure'),Output('msft-box','children'), Output('tsla-box','children')],[Input('interval-component', 'n_intervals')])
def update_graph(n):
    weather = get_meteo_data()
    weather = weather.rename(columns = {"time":"Date", "temperature_2m_max":"Max temp", "temperature_2m_min":"Min temp", 
    "precipitation_probability_max":"Precipitation Probability"})
    weather['Date'] = pd.to_datetime(weather.Date)
    weather = weather.set_index('Date')

    # Get stock data
    msft_data = get_stock_data('MSFT')
    tsla_data = get_stock_data('TSLA')

    #weekly change for stocks
    msft_percentage_change = ((msft_data.iloc[-1] - msft_data.iloc[0]) / msft_data.iloc[0]) * 100
    tsla_percentage_change = ((tsla_data.iloc[-1] - tsla_data.iloc[0]) / tsla_data.iloc[0]) * 100
    min_temp = weather['Min temp']
    max_temp = weather['Max temp']
    precip_prob = weather['Precipitation Probability']

    # Alerts
    if msft_percentage_change >= abs(10):
        EmailService().send("sarthakraheja13@gmail.com","Microsoft large price change alert",f"Microsoft changed {msft_percentage_change}% in the last seven days")

    if tsla_percentage_change >= abs(10):
        EmailService().send("sarthakraheja13@gmail.com","Tesla large price change alert",f"Tesla changed {tsla_percentage_change}% in the last seven days")

    if precip_prob.max() >= abs(50):
        EmailService().send("sarthakraheja13@gmail.com","Rain alert",f"There is {precip_prob.max()}% chance of rain in the coming seven days")


    # Create 2x2 subplots with custom spacing
    fig = make_subplots(rows=2, cols=2, subplot_titles=('MSFT over 7 days', 'TSLA over 7 days', 'Temperature for next 7 days', 'Precipitation Probability'),
                        vertical_spacing=0.15, horizontal_spacing=0.1)

    # Add plots to the subplots
    fig.add_trace(go.Scatter(x=msft_data.index, y=msft_data.values, name='MSFT'), row=1, col=1)
    fig.add_trace(go.Scatter(x=tsla_data.index, y=tsla_data.values, name='TSLA'), row=1, col=2)
    fig.add_trace(go.Scatter(x=min_temp.index, y=min_temp, name='Min Temp'), row=2, col=1)
    fig.add_trace(go.Scatter(x=max_temp.index, y=max_temp, name='Max Temp'), row=2, col=1)
    fig.add_trace(go.Bar(x=precip_prob.index, y=precip_prob, name='Precipitation Probability'), row=2, col=2)

    # Update xaxis properties
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="Price in USD", row=1, col=1)
    fig.update_yaxes(title_text="Price in USD", row=1, col=2)
    fig.update_yaxes(title_text="Fahrenheit", row=2, col=1)
    fig.update_yaxes(title_text="Probability Percentage", row=2, col=2)

    # Adjust the overall size of the plot
    fig.update_layout(title_text = "Personalized Dashboard",title_x=0.4, title_xanchor = "center", title_font= dict(size=24), height=800, width=1000)

    return fig, f'MSFT Weekly Change: {msft_percentage_change:.2f}%', f'TSLA Weekly Change: {tsla_percentage_change:.2f}%'


app.layout = html.Div([
    dcc.Graph(
        id='subplot-graph',
        figure = {},
        style={'width': '1000px', 'margin': 'auto'}  # This is to align the graph in center
    ),
    html.Div([
        html.Div(id ='msft-box', style=box_style),
        html.Div(id = 'tsla-box', style=box_style)
    ], style={'display': 'flex', 'width': '1000px', 'margin': 'auto'}),
    dcc.Interval(id = 'interval-component', interval = 1000*3600, n_intervals = 0)  
])


if __name__ == '__main__':
    app.run_server(debug=True, port = 8040)