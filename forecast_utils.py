import pandas as pd
import plotly.graph_objs as go
import plotly
import json

def generate_forecast_plot(data_file):
    forecast_data = pd.read_csv(data_file)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=forecast_data['Date'], 
        y=forecast_data['EV_Demand'], 
        mode='lines+markers',
        name='EV Demand'
    ))

    fig.update_layout(
        title='Electric Vehicle Demand Forecast Over Time',
        xaxis_title='Date',
        yaxis_title='Predicted EV Demand',
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder), forecast_data.describe().to_string()