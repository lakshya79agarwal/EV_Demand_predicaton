import pandas as pd
import plotly.express as px
import json
import plotly.utils

def generate_forecast_plot(data_file):
    # 1. Load the Data
    df = pd.read_csv(data_file)
    
    # 2. Fix Date Format
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 3. THE FIX: Group by Date and Sum
    # This combines all 269 counties into ONE total number per month
    df_grouped = df.groupby('Date')['Electric Vehicle (EV) Total'].sum().reset_index()
    
    # 4. Sort by Date (Crucial for a smooth line)
    df_grouped = df_grouped.sort_values('Date')

    # 5. Create the Plot using the GROUPED dataframe
    fig = px.line(
        df_grouped, 
        x='Date', 
        y='Electric Vehicle (EV) Total', 
        title='Total National EV Demand (All Counties Aggregated)',
        labels={'Electric Vehicle (EV) Total': 'Total EV Demand'}
    )
    
    # Make the graph look professional
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Vehicles",
        template="plotly_white"
    )

    # 6. Convert to JSON for Flask
    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # 7. Generate Summary for the AI
    latest_date = df_grouped.iloc[-1]['Date'].strftime('%Y-%m-%d')
    latest_val = int(df_grouped.iloc[-1]['Electric Vehicle (EV) Total'])
    summary = f"The graph displays the aggregated EV demand. As of {latest_date}, the total demand is {latest_val:,} vehicles."

    return plot_json, summary
