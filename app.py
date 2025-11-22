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

# ---------------------------------------------------------
# 2. AUTHENTICATION (Security Gate)
# ---------------------------------------------------------
# Ensure auth.py is in the same folder
try:
    from auth import check_password
    
    # If password is incorrect, stop the app here.
    # The user will only see the login screen.
    if not check_password():
        st.stop()
except ImportError:
    st.error("❌ 'auth.py' not found. Please ensure the authentication script is in the project folder.")
    st.stop()

# =========================================================
# 🚀 MAIN APP STARTS HERE (Only runs if logged in)
# =========================================================

# ---------------------------------------------------------
# 3. GOOGLE GEMINI API SETUP
# ---------------------------------------------------------
# Priority: Streamlit secrets, then .env / environment variable
api_key = st.secrets.get("GOOGLE_API_KEY") if hasattr(st, "secrets") else None
api_key = api_key or os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.sidebar.error("⚠ GOOGLE_API_KEY is missing from Secrets/Environment. Chat will be disabled.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"API Key Configuration Failed: {e}")

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
# 4. DATA LOADING & PROCESSING
# ---------------------------------------------------------
REQUIRED_COLUMNS = [
    "Date",
    "State",
    "Electric Vehicle (EV) Total",
    "Battery Electric Vehicles (BEVs)",
    "Plug-In Hybrid Electric Vehicles (PHEVs)"
]

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("preprocessed_ev_data.csv")
        # Check required columns exist
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise KeyError(f"Missing columns in CSV: {missing}")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {e}"

raw_df = load_data()

if isinstance(raw_df, str):
    if raw_df == "FILE_NOT_FOUND":
        st.error("❌ Data file 'preprocessed_ev_data.csv' not found. "
                 "Place it in the same folder as app.py and ensure it has the required columns.")
    else:
        st.error(f"❌ Error loading data: {raw_df}")
    st.stop()

# ---------------------------------------------------------
# 5. SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")

# Add a logout button to the sidebar
if st.sidebar.button("Log Out"):
    st.session_state["password_correct"] = False
    st.rerun()

st.sidebar.divider()

all_states = sorted(raw_df["State"].unique().tolist())
selected_state = st.sidebar.multiselect(
    "Select State",
    all_states,
    default=all_states[:1] if all_states else []
)

if not selected_state:
    st.sidebar.info("No state selected. Showing all states.")
    filtered_df = raw_df.copy()
else:
    filtered_df = raw_df[raw_df["State"].isin(selected_state)]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Daily aggregation for charts & AI context
daily_agg = (
    filtered_df
    .groupby("Date")[
        [
            "Electric Vehicle (EV) Total",
            "Battery Electric Vehicles (BEVs)",
            "Plug-In Hybrid Electric Vehicles (PHEVs)"
        ]
    ]
    .sum()
    .reset_index()
    .sort_values("Date")
)

# ---------------------------------------------------------
# 6. MAIN DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "🤖 AI Analyst", "📄 Raw Data"])

# =======================
# TAB 1: DASHBOARD
# =======================
with tab1:
    if not daily_agg.empty:
        latest_record = daily_agg.iloc[-1]
        prev_record = daily_agg.iloc[-2] if len(daily_agg) > 1 else latest_record

        total_ev = int(latest_record["Electric Vehicle (EV) Total"])
        prev_total_ev = int(prev_record["Electric Vehicle (EV) Total"])

        growth = total_ev - prev_total_ev
        growth_pct = (growth / prev_total_ev * 100) if prev_total_ev > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Total EV Demand (Selected)",
            f"{total_ev:,}",
            delta=f"{growth_pct:.1f}% Growth"
        )
        col2.metric(
            "Battery EVs (BEV)",
            f"{int(latest_record['Battery Electric Vehicles (BEVs)']):,}"
        )
        col3.metric(
            "Plug-in Hybrids (PHEV)",
            f"{int(latest_record['Plug-In Hybrid Electric Vehicles (PHEVs)']):,}"
        )
    else:
        st.warning("No aggregated data available for the selected filters.")

    st.divider()

    # Charts row
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Demand Trend Over Time")
        if not daily_agg.empty:
            fig_line = px.line(
                daily_agg,
                x="Date",
                y="Electric Vehicle (EV) Total",
                markers=True,
                template="plotly_white",
                labels={"Electric Vehicle (EV) Total": "Number of Vehicles"},
                title="Total EV Demand Over Time"
            )
            fig_line.update_traces(line_width=3)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No data to display in the trend chart.")

    with c2:
        st.subheader("Vehicle Type Split")
        if not daily_agg.empty:
            total_bev = daily_agg["Battery Electric Vehicles (BEVs)"].sum()
            total_phev = daily_agg["Plug-In Hybrid Electric Vehicles (PHEVs)"].sum()

            pie_data = pd.DataFrame({
                "Type": ["BEV", "PHEV"],
                "Count": [total_bev, total_phev]
            })

            fig_pie = px.pie(
                pie_data,
                names="Type",
                values="Count",
                hole=0.4,
                title="BEV vs PHEV Share"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data to display in the pie chart.")

# =======================
# TAB 2: AI ANALYST
# =======================
with tab2:
    st.subheader("💬 Chat with your Data")
    st.write("Ask about EV demand trends, predictions, or comparisons between BEVs and PHEVs.")

    if not daily_agg.empty:
        latest_date_str = daily_agg.iloc[-1]["Date"].strftime("%Y-%m-%d")
        latest_val = int(daily_agg.iloc[-1]["Electric Vehicle (EV) Total"])
        context = (
            f"Data Context: EV demand for the selected states from "
            f"{daily_agg.iloc[0]['Date'].date()} to {latest_date_str}. "
            f"As of {latest_date_str}, total EV demand is {latest_val:,} vehicles. "
            f"The data is aggregated by date for Electric Vehicle (EV) Total, "
            f"Battery Electric Vehicles (BEVs), and Plug-In Hybrid Electric Vehicles (PHEVs)."
        )
    else:
        context = "No data selected."

    user_query = st.chat_input("Ask about EV demand trends, future predictions, or insights...")

    if user_query:
        st.chat_message("user").write(user_query)

        if not api_key:
            st.error("❌ API Key missing. Configure GOOGLE_API_KEY in secrets or environment.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Connecting to Google AI..."):
                    try:
                        # PRIMARY MODEL: New fast model
                        try:
                            model = genai.GenerativeModel("gemini-2.0-flash")
                            response = model.generate_content(
                                f"{context}\n\nThe user asked: {user_query}\n\n"
                                f"Use the context to answer clearly and briefly."
                            )
                        except Exception as e1:
                            # FALLBACK MODEL: More powerful 1.5 Pro
                            st.warning(f"⚠ gemini-2.0-flash failed ({e1}), trying gemini-1.5-pro...")
                            model = genai.GenerativeModel("gemini-1.5-pro")
                            response = model.generate_content(
                                f"{context}\n\nThe user asked: {user_query}\n\n"
                                f"Use the context to answer clearly and briefly."
                            )

                        st.write(response.text)

                    except Exception as e2:
                        st.error(f"❌ Chat Failed. Reason: {e2}")
                        st.write("Check your API Key, model access, or quota in Google AI Studio.")

# =======================
# TAB 3: RAW DATA
# =======================
with tab3:
    st.subheader("Raw Data Explorer")
    st.dataframe(filtered_df)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered CSV",
        data=csv,
        file_name="ev_data_filtered.csv",
        mime="text/csv",
    )
