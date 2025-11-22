import streamlit as st
import pandas as pd
import plotly.express as px
import os
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. APP CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="EV Demand Dashboard",
    page_icon="⚡",
    layout="wide"
)
load_dotenv()

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SETUP GOOGLE GEMINI
# ---------------------------------------------------------
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.sidebar.error("⚠️ Google API Key missing! Chat will be disabled.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"API Key Error: {e}")

# ---------------------------------------------------------
# 3. DATA LOADING & PROCESSING
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('preprocessed_ev_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        return None

raw_df = load_data()

if raw_df is None:
    st.error("❌ Data file 'preprocessed_ev_data.csv' not found. Please upload it to your repository.")
    st.stop()

# ---------------------------------------------------------
# 4. SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")

# State Filter
all_states = sorted(raw_df['State'].unique())
selected_state = st.sidebar.multiselect("Select State", all_states, default=all_states[:1]) # Default to first state to avoid messy graph initially

# Filter Logic
if not selected_state:
    st.sidebar.warning("Select at least one state to view data.")
    filtered_df = raw_df.copy()
else:
    filtered_df = raw_df[raw_df['State'].isin(selected_state)]

# Aggregate Data (Crucial to prevent overlapping lines)
# We group by Date to get a single clean trend line for the selection
daily_agg = filtered_df.groupby('Date')[['Electric Vehicle (EV) Total', 'Battery Electric Vehicles (BEVs)', 'Plug-In Hybrid Electric Vehicles (PHEVs)']].sum().reset_index()
daily_agg = daily_agg.sort_values('Date')

# ---------------------------------------------------------
# 5. MAIN DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

# Create Tabs
tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "🤖 AI Analyst", "📄 Raw Data"])

# --- TAB 1: DASHBOARD ---
with tab1:
    # KPI Metrics
    if not daily_agg.empty:
        latest_record = daily_agg.iloc[-1]
        prev_record = daily_agg.iloc[-2] if len(daily_agg) > 1 else latest_record
        
        total_ev = int(latest_record['Electric Vehicle (EV) Total'])
        growth = total_ev - int(prev_record['Electric Vehicle (EV) Total'])
        growth_pct = (growth / prev_record['Electric Vehicle (EV) Total']) * 100 if prev_record['Electric Vehicle (EV) Total'] > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total EV Demand (Selected)", f"{total_ev:,}", delta=f"{growth_pct:.1f}% Growth")
        col2.metric("Battery EVs (BEV)", f"{int(latest_record['Battery Electric Vehicles (BEVs)']):,}")
        col3.metric("Plug-in Hybrids (PHEV)", f"{int(latest_record['Plug-In Hybrid Electric Vehicles (PHEVs)']):,}")

    st.divider()

    # Charts Row
    c1, c2 = st.columns([2, 1]) # 2:1 ratio for chart width

    with c1:
        st.subheader("Demand Trend Over Time")
        fig_line = px.line(
            daily_agg, 
            x='Date', 
            y='Electric Vehicle (EV) Total',
            markers=True,
            template="plotly_white",
            labels={'Electric Vehicle (EV) Total': 'Number of Vehicles'}
        )
        fig_line.update_traces(line_color='#00CC96', line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("Vehicle Type Split")
        # Summing up total BEV vs PHEV for the Pie Chart
        total_bev = daily_agg['Battery Electric Vehicles (BEVs)'].sum()
        total_phev = daily_agg['Plug-In Hybrid Electric Vehicles (PHEVs)'].sum()
        
        pie_data = pd.DataFrame({
            'Type': ['BEV', 'PHEV'],
            'Count': [total_bev, total_phev]
        })
        
        fig_pie = px.pie(pie_data, names='Type', values='Count', hole=0.4, color_discrete_sequence=['#636EFA', '#EF553B'])
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 2: AI ANALYST ---
with tab2:
    st.subheader("💬 Chat with your Data")
    st.write("Ask questions like: *'What is the peak demand month?'* or *'Compare BEV vs PHEV trends.'*")
    
    # Prepare Context
    if not daily_agg.empty:
        latest_date_str = daily_agg.iloc[-1]['Date'].strftime('%Y-%m-%d')
        latest_val = int(daily_agg.iloc[-1]['Electric Vehicle (EV) Total'])
        context = f"Data Context: Analysis of EV Demand from {daily_agg.iloc[0]['Date'].date()} to {latest_date_str}. Latest aggregated demand is {latest_val:,} vehicles."
    else:
        context = "No data selected."

    # Chat Input
    user_query = st.chat_input("Type your question here...")

    if user_query:
        st.chat_message("user").write(user_query)
        
        if not api_key:
            st.error("❌ Please configure GOOGLE_API_KEY in your secrets to use the AI.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        # Robust Model Selection (Flash -> Pro fallback)
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(f"{context}\n\nUser Question: {user_query}")
                        except:
                            model = genai.GenerativeModel('gemini-pro')
                            response = model.generate_content(f"{context}\n\nUser Question: {user_query}")
                        
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"AI Error: {e}")

# --- TAB 3: RAW DATA ---
with tab3:
    st.subheader("Raw Data Explorer")
    st.dataframe(filtered_df)
    
    # Download Button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered CSV",
        data=csv,
        file_name='ev_data_filtered.csv',
        mime='text/csv',
    )
