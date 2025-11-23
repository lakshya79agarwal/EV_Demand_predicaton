import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # NEW: For combined plots
import os
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression # NEW: ML Model

# ---------------------------------------------------------
# 1. APP CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="EV Demand Dashboard", page_icon="⚡", layout="wide")
load_dotenv()

# ---------------------------------------------------------
# 2. AUTHENTICATION
# ---------------------------------------------------------
try:
    from auth import check_password
    if not check_password():
        st.stop()
except ImportError:
    st.error("❌ 'auth.py' not found.")
    st.stop()

# ---------------------------------------------------------
# 3. API & DATA SETUP
# ---------------------------------------------------------
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"API Error: {e}")

REQUIRED_COLUMNS = ["Date", "State", "Electric Vehicle (EV) Total", "Battery Electric Vehicles (BEVs)", "Plug-In Hybrid Electric Vehicles (PHEVs)"]

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("preprocessed_ev_data.csv")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except Exception as e:
        return str(e)

raw_df = load_data()
if isinstance(raw_df, str):
    st.error(f"❌ Error loading data: {raw_df}")
    st.stop()

# ---------------------------------------------------------
# 4. MACHINE LEARNING FUNCTION
# ---------------------------------------------------------
def predict_future(df_agg, months_to_predict=24):
    # 1. Prepare Data
    df_ml = df_agg.copy()
    # Convert Date to ordinal number (so the model can understand it)
    df_ml['Date_Ordinal'] = df_ml['Date'].map(pd.Timestamp.toordinal)
    
    X = df_ml[['Date_Ordinal']]
    y = df_ml['Electric Vehicle (EV) Total']
    
    # 2. Train Model
    model = LinearRegression()
    model.fit(X, y)
    
    # 3. Create Future Dates
    last_date = df_ml['Date'].max()
    future_dates = [last_date + timedelta(days=x*30) for x in range(1, months_to_predict + 1)]
    future_ordinals = [[d.toordinal()] for d in future_dates]
    
    # 4. Predict
    future_pred = model.predict(future_ordinals)
    
    # 5. Create DataFrame for Forecast
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Predicted Demand': future_pred,
        'Type': 'Forecast'
    })
    
    # Label original data
    original_df = df_agg[['Date', 'Electric Vehicle (EV) Total']].copy()
    original_df.columns = ['Date', 'Predicted Demand'] # Rename for merging
    original_df['Type'] = 'Historical'
    
    return pd.concat([original_df, forecast_df], ignore_index=True), model

# ---------------------------------------------------------
# 5. SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("Filters")
if st.sidebar.button("Log Out"):
    st.session_state["password_correct"] = False
    st.rerun()
st.sidebar.divider()

all_states = sorted(raw_df["State"].unique().tolist())
selected_state = st.sidebar.multiselect("Select State", all_states, default=all_states[:1] if all_states else [])

if not selected_state:
    filtered_df = raw_df.copy()
else:
    filtered_df = raw_df[raw_df["State"].isin(selected_state)]

# Aggregate Data
daily_agg = filtered_df.groupby("Date")[["Electric Vehicle (EV) Total", "Battery Electric Vehicles (BEVs)", "Plug-In Hybrid Electric Vehicles (PHEVs)"]].sum().reset_index().sort_values("Date")

# ---------------------------------------------------------
# 6. DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

# NEW TAB: Future Prediction
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dashboard", "🔮 Future Prediction", "🤖 AI Analyst", "📄 Raw Data", "📝 Feedback"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if not daily_agg.empty:
        latest = daily_agg.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("Total EV Demand", f"{int(latest['Electric Vehicle (EV) Total']):,}")
        col2.metric("Battery EVs", f"{int(latest['Battery Electric Vehicles (BEVs)']):,}")
        col3.metric("Plug-in Hybrids", f"{int(latest['Plug-In Hybrid Electric Vehicles (PHEVs)']):,}")
        
        st.subheader("Historical Trends")
        fig = px.line(daily_agg, x="Date", y="Electric Vehicle (EV) Total", markers=True, title="Past Demand")
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: FUTURE PREDICTION (ML) ---
with tab2:
    st.subheader("🔮 Future Demand Forecast (Linear Regression)")
    st.write("This chart uses Linear Regression to project EV sales for the next 2 years based on historical patterns.")
    
    if not daily_agg.empty:
        # Run Prediction
        forecast_combined, model = predict_future(daily_agg)
        
        # Calculate simple stats
        slope = model.coef_[0]
        trend_text = "Increasing" if slope > 0 else "Decreasing"
        
        st.info(f"📈 **Trend Analysis:** The model detects an **{trend_text}** trend of approximately **{int(slope * 30)} new vehicles per month**.")

        # Plot combined data
        fig_forecast = px.line(
            forecast_combined, 
            x="Date", 
            y="Predicted Demand", 
            color="Type", 
            markers=True,
            color_discrete_map={"Historical": "blue", "Forecast": "green"}
        )
        fig_forecast.update_traces(line=dict(width=3))
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.warning("Not enough data to generate a prediction.")

# --- TAB 3: AI ANALYST ---
with tab3:
    st.subheader("💬 Chat with your Data")
    user_query = st.chat_input("Ask about trends...")
    if user_query and api_key:
        with st.chat_message("assistant"):
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                # Pass the forecast context to the AI too!
                if not daily_agg.empty:
                    forecast_combined, _ = predict_future(daily_agg)
                    future_val = int(forecast_combined.iloc[-1]['Predicted Demand'])
                    context = f"Based on Linear Regression, the predicted demand in 2 years is approx {future_val} vehicles."
                else:
                    context = ""
                    
                response = model.generate_content(f"Context: {context}. User Question: {user_query}")
                st.write(response.text)
            except Exception as e:
                st.error(f"AI Error: {e}")

# --- TAB 4: RAW DATA ---
with tab4:
    st.dataframe(filtered_df)

# --- TAB 5: FEEDBACK ---
with tab5:
    st.subheader("💾 Feedback & Database")
    with st.form("feedback"):
        name = st.text_input("Name")
        msg = st.text_area("Message")
        if st.form_submit_button("Submit"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                existing = conn.read(worksheet="Sheet1", usecols=[0,1,2], ttl=5)
                new = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Name": name, "Feedback": msg}])
                updated = pd.concat([existing, new], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated)
                st.success("Saved!")
            except Exception as e:
                st.error(f"Database Error: {e}")
