import streamlit as st
import pandas as pd
import plotly.express as px
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Config & Setup
st.set_page_config(page_title="EV Demand Predictor", layout="wide")
load_dotenv()

# --- DEBUG CHECK ---
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY is missing from Secrets/Environment. Chat cannot work.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API Key Configuration Failed: {e}")

# 2. Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('preprocessed_ev_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df_grouped = df.groupby('Date')['Electric Vehicle (EV) Total'].sum().reset_index()
        df_grouped = df_grouped.sort_values('Date')
        return df_grouped
    except Exception as e:
        return None

df = load_data()

# 3. Display Dashboard
if df is not None:
    st.title("🚗 EV Demand Prediction Dashboard")
    
    fig = px.line(df, x='Date', y='Electric Vehicle (EV) Total', title='Total EV Demand')
    st.plotly_chart(fig, use_container_width=True)

    # 4. Chat Section
    st.divider()
    st.subheader("🤖 AI Chat Analyst")

    # Prepare context
    latest_date = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
    latest_val = int(df.iloc[-1]['Electric Vehicle (EV) Total'])
    context = f"Data Context: EV Demand as of {latest_date} is {latest_val:,} vehicles."

    user_query = st.chat_input("Ask about the data...")

    if user_query:
        st.write(f"**You:** {user_query}")
        
        if not api_key:
            st.error("❌ API Key missing.")
        else:
            with st.spinner("Connecting to Google AI..."):
                try:
                    # TRY MODEL 1: 1.5 Flash (Newest/Fastest)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"{context}\nQuestion: {user_query}")
                    st.write(f"**AI:** {response.text}")
                except Exception as e1:
                    # FAILBACK TO MODEL 2: Pro (Standard)
                    try:
                        st.warning(f"Flash model failed ({e1}), trying gemini-pro...")
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content(f"{context}\nQuestion: {user_query}")
                        st.write(f"**AI:** {response.text}")
                    except Exception as e2:
                        st.error(f"❌ Chat Failed. Reason: {e2}")
                        st.write("Check your API Key permissions or Quota.")
else:
    st.error("Data file not found.")
