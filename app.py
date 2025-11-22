import streamlit as st
import pandas as pd
import plotly.express as px
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Config & Setup
st.set_page_config(page_title="EV Demand Predictor", layout="wide")
load_dotenv()

# CONFIGURATION: Setup Google Gemini
# Try to get key from Streamlit Secrets first, then Environment Variable
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("⚠️ GOOGLE_API_KEY is missing. Chat feature will not work.")

# 2. Load and Process Data
@st.cache_data
def load_data():
    try:
        # Load the file
        df = pd.read_csv('preprocessed_ev_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        
        # AGGREGATE DATA (Fixes overlapping lines)
        # We sum up the demand for all counties to get one national total per month
        df_grouped = df.groupby('Date')['Electric Vehicle (EV) Total'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Date')
        return df_grouped
    except Exception as e:
        return None

df = load_data()

# 3. Display the Dashboard
if df is not None:
    st.title("🚗 EV Demand Prediction Dashboard")
    
    # Show the Plot
    fig = px.line(
        df, 
        x='Date', 
        y='Electric Vehicle (EV) Total', 
        title='Total National EV Demand (Aggregated)',
        labels={'Electric Vehicle (EV) Total': 'Total Vehicles'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # 4. AI Analysis Section (Powered by Gemini)
    st.divider()
    st.subheader("🤖 Ask the AI Analyst (Google Gemini)")

    # Prepare summary for the AI
    latest_date = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
    latest_val = int(df.iloc[-1]['Electric Vehicle (EV) Total'])
    summary_context = f"The data shows aggregated EV demand. As of {latest_date}, total demand is {latest_val:,} vehicles."

    # Chat Interface
    user_query = st.chat_input("Ask a question about the trend (e.g., 'Is demand increasing?')")

    if user_query:
        # Show user message
        with st.chat_message("user"):
            st.write(user_query)

        # Generate and show AI response
        with st.chat_message("assistant"):
            if not api_key:
                st.error("Please set your GOOGLE_API_KEY to use the chat.")
            else:
                with st.spinner("Thinking..."):
                    try:
                        # --- UPDATED MODEL HERE ---
                        # Using 'gemini-pro' instead of 'gemini-1.5-flash' for better compatibility
                        model = genai.GenerativeModel('gemini-pro')
                        
                        # Create prompt
                        full_prompt = f"Context: {summary_context}\n\nUser Question: {user_query}\n\nAnswer as a data analyst:"
                        
                        response = model.generate_content(full_prompt)
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Error: {e}")

else:
    st.error("❌ Could not find 'preprocessed_ev_data.csv'. Make sure it is in the root folder.")
