import streamlit as st
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
# Priority: Streamlit secrets, then .env / environment variable
api_key = st.secrets.get("GOOGLE_API_KEY") if hasattr(st, "secrets") else None
api_key = api_key or os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠ GOOGLE_API_KEY is missing from Secrets/Environment. Chat cannot work.")
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
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

# 3. Display Dashboard
if df is not None and not df.empty:
    st.title("🚗 EV Demand Prediction Dashboard")
    
    fig = px.line(
        df,
        x='Date',
        y='Electric Vehicle (EV) Total',
        title='Total EV Demand Over Time'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 4. Chat Section
    st.divider()
    st.subheader("🤖 AI Chat Analyst")

    # Prepare context from latest data point
    latest_date = df.iloc[-1]['Date'].strftime('%Y-%m-%d')
    latest_val = int(df.iloc[-1]['Electric Vehicle (EV) Total'])
    context = f"Data Context: EV Demand as of {latest_date} is {latest_val:,} vehicles."

    user_query = st.chat_input("Ask about the EV demand trends, future predictions, or insights...")

    if user_query:
        st.write(f"You: {user_query}")
        
        if not api_key:
            st.error("❌ API Key missing.")
        else:
            with st.spinner("Connecting to Google AI..."):
                try:
                    # PRIMARY MODEL: New fast model
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    response = model.generate_content(
                        f"{context}\n\nThe user asked: {user_query}\n\n"
                        f"Use the context to answer clearly and briefly."
                    )
                    st.write(f"AI: {response.text}")
                except Exception as e1:
                    # FALLBACK MODEL: More powerful 1.5 Pro
                    try:
                        st.warning(f"⚠ gemini-2.0-flash failed ({e1}), trying gemini-1.5-pro...")
                        model = genai.GenerativeModel("gemini-1.5-pro")
                        response = model.generate_content(
                            f"{context}\n\nThe user asked: {user_query}\n\n"
                            f"Use the context to answer clearly and briefly."
                        )
                        st.write(f"AI: {response.text}")
                    except Exception as e2:
                        st.error(f"❌ Chat Failed. Reason: {e2}")
                        st.write("Check your API Key, model access, or quota in Google AI Studio.")
else:
    st.error("Data file not found or is empty. Make sure 'preprocessed_ev_data.csv' exists in the same folder and has a 'Date' and 'Electric Vehicle (EV) Total' column.")
