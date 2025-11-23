# /mount/src/ev_demand_predicaton/app.py
"""
EV Demand Dashboard - corrected & complete
Save as: /mount/src/ev_demand_predicaton/app.py
Requirements:
  pip install streamlit pandas plotly python-dotenv google-generativeai streamlit-gsheets
(or adapt to your connector choice)
"""

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# 1. APP CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="EV Demand Dashboard",
    page_icon="⚡",
    layout="wide",
)

# Load environment variables
load_dotenv()

# ---------------------------------------------------------
# CUSTOM CSS FOR DARK (BLACK) METRIC BACKGROUND
# (placed early so CSS is applied before layout renders)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Make metric boxes black */
    div[data-testid="metric-container"] {
        background-color: #000000 !important;
        padding: 18px 20px !important;
        border-radius: 12px;
        color: white !important;
        border: 1px solid #2b2b2b !important;
    }

    /* Metric label & value color */
    div[data-testid="metric-container"] > label,
    div[data-testid="metric-container"] > div {
        color: #ffffff !important;
    }

    /* Page background (top area) */
    .stApp {
        background-color: #0b0b0b !important;
    }

    /* Tabs area background */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0b0b0b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. AUTHENTICATION (Security Gate)
# ---------------------------------------------------------
try:
    from auth import check_password

    if not check_password():
        st.stop()
except ImportError:
    st.error("❌ 'auth.py' not found — authentication disabled. Create an auth.py with check_password().")
    st.stop()

# ---------------------------------------------------------
# 3. GOOGLE GEMINI (Generative AI) API SETUP
# ---------------------------------------------------------
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.sidebar.error("⚠ GOOGLE_API_KEY is missing in streamlit secrets or environment variables.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"API Key Error: {e}")

# ---------------------------------------------------------
# 4. DATA LOADING
# ---------------------------------------------------------
REQUIRED_COLUMNS = [
    "Date",
    "State",
    "Electric Vehicle (EV) Total",
    "Battery Electric Vehicles (BEVs)",
    "Plug-In Hybrid Electric Vehicles (PHEVs)",
]


@st.cache_data
def load_data(path: str = "preprocessed_ev_data.csv"):
    try:
        df = pd.read_csv(path)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
        else:
            raise ValueError("Missing 'Date' column in CSV.")
        # Optionally ensure required columns exist
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Required columns missing from CSV: {missing}")
        return df
    except Exception as e:
        # Return an exception message string for caller to handle
        return str(e)


raw_df = load_data()
if isinstance(raw_df, str):
    st.error(f"❌ Error loading data: {raw_df}")
    st.stop()

# ---------------------------------------------------------
# 5. SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")
if st.sidebar.button("Log Out"):
    st.session_state["password_correct"] = False
    st.experimental_rerun()
st.sidebar.divider()

all_states = sorted(raw_df["State"].unique().tolist())
selected_state = st.sidebar.multiselect(
    "Select State", all_states, default=all_states[:1] if all_states else []
)

if not selected_state:
    filtered_df = raw_df.copy()
else:
    filtered_df = raw_df[raw_df["State"].isin(selected_state)]

# aggregate daily numbers for charts/metrics
daily_agg = (
    filtered_df.groupby("Date")[
        ["Electric Vehicle (EV) Total", "Battery Electric Vehicles (BEVs)", "Plug-In Hybrid Electric Vehicles (PHEVs)"]
    ]
    .sum()
    .reset_index()
    .sort_values("Date")
)

# ---------------------------------------------------------
# Helper: establish a gsheets connection in a version-agnostic way
# ---------------------------------------------------------
def get_gsheets_conn():
    """Try modern and experimental Streamlit connection APIs."""
    last_exc = None
    try:
        # modern API (Streamlit >= some version)
        return st.connections.connect("gsheets", type=GSheetsConnection)
    except Exception as e:
        last_exc = e
    try:
        # fallback older API
        return st.experimental_connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        last_exc = e
    # If we couldn't get a connection, raise the last exception to report to the user
    raise last_exc


# ---------------------------------------------------------
# 6. MAIN DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "🤖 AI Analyst", "📄 Raw Data", "📝 Feedback (Database)"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if not daily_agg.empty:
        latest = daily_agg.iloc[-1]
        col1, col2, col3 = st.columns(3)
        # Use try/except because values might be NaN or float
        try:
            col1.metric("Total EV Demand", f"{int(latest['Electric Vehicle (EV) Total']):,}")
        except Exception:
            col1.metric("Total EV Demand", latest.get("Electric Vehicle (EV) Total", "N/A"))
        try:
            col2.metric("Battery EVs", f"{int(latest['Battery Electric Vehicles (BEVs)']):,}")
        except Exception:
            col2.metric("Battery EVs", latest.get("Battery Electric Vehicles (BEVs)", "N/A"))
        try:
            col3.metric("Plug-in Hybrids", f"{int(latest['Plug-In Hybrid Electric Vehicles (PHEVs)']):,}")
        except Exception:
            col3.metric("Plug-in Hybrids", latest.get("Plug-In Hybrid Electric Vehicles (PHEVs)", "N/A"))

        st.subheader("Demand Trend")
        fig = px.line(daily_agg, x="Date", y="Electric Vehicle (EV) Total", markers=True)
        # Make plotly charts dark-friendly
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

# --- TAB 2: AI ANALYST ---
with tab2:
    st.subheader("💬 Chat with your Data")
    user_query = st.chat_input("Ask about trends...")
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)

        if api_key:
            with st.chat_message("assistant"):
                try:
                    # Try a few invocation styles for compatibility
                    ai_text = None
                    if hasattr(genai, "GenerativeModel"):
                        # older style
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(f"User asked: {user_query}. Context: EV Data.")
                        ai_text = getattr(response, "text", None) or getattr(response, "output", None) or str(response)
                    elif hasattr(genai, "generate_text"):
                        # newer style helper
                        response = genai.generate_text(model="gemini-1.5-flash", input=f"User asked: {user_query}. Context: EV Data.")
                        ai_text = getattr(response, "text", None) or getattr(response, "output", None) or str(response)
                    else:
                        ai_text = "AI client library is present but API shape is unknown. Check google.generativeai version."

                    st.write(ai_text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.info("No API key found for the AI model. Set GOOGLE_API_KEY in Streamlit secrets or environment variables.")

# --- TAB 3: RAW DATA ---
with tab3:
    st.dataframe(filtered_df)

# --- TAB 4: FEEDBACK (DATA PERSISTENCE) ---
with tab4:
    st.subheader("💾 Persistent Data Storage")
    st.write("Submit feedback or feature requests. This data is saved permanently to Google Sheets.")

    with st.form("feedback_form"):
        name = st.text_input("Your Name")
        feedback = st.text_area("Feedback / Request")
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            try:
                conn = get_gsheets_conn()

                # Try reading the sheet; connector may return a DataFrame or raise
                existing_data = None
                try:
                    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(3)), ttl=5)
                except Exception:
                    # Some connector implementations raise or return None for an empty sheet
                    existing_data = None

                if existing_data is None:
                    existing_data = pd.DataFrame(columns=["Date", "Name", "Feedback"])

                new_entry = pd.DataFrame(
                    [
                        {
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Name": name,
                            "Feedback": feedback,
                        }
                    ]
                )

                updated_df = pd.concat([existing_data, new_entry], ignore_index=True)

                # Update sheet (connector expects a DataFrame or similar)
                conn.update(worksheet="Sheet1", data=updated_df)

                st.success("✅ Feedback saved to Database!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
                st.info(
                    "Make sure you have set up 'connections.gsheets' in Streamlit secrets, configured the connector, "
                    "and installed the required packages."
                )
