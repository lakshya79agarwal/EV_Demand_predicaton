# /mount/src/ev_demand_predicaton/app.py
"""
EV Demand Dashboard - Final Robust Version

Requirements:
  pip install streamlit pandas plotly python-dotenv google-generativeai streamlit-gsheets gspread oauth2client
"""

import os
import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Optional import for streamlit-gsheets connector type hinting
try:
    from streamlit_gsheets import GSheetsConnection
except Exception:
    GSheetsConnection = None  # connector type may be unavailable; we fallback to gspread

# ---------------------------------------------------------
# 1. APP CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="EV Demand Dashboard", page_icon="⚡", layout="wide")
load_dotenv()

# ---------------------------------------------------------
# 2. CUSTOM CSS (Styling metrics and background)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    div[data-testid="metric-container"] {
        background-color: #000000 !important;
        padding: 18px 20px !important;
        border-radius: 12px;
        color: white !important;
        border: 1px solid #2b2b2b !important;
    }
    div[data-testid="metric-container"] > label,
    div[data-testid="metric-container"] > div {
        color: #ffffff !important;
    }
    .stApp {
        background-color: #0b0b0b !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0b0b0b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. AUTHENTICATION (Optional)
# ---------------------------------------------------------
try:
    from auth import check_password

    if not check_password():
        st.stop()
except ImportError:
    # If auth.py doesn't exist, we skip auth but warn the user locally
    # st.warning("⚠️ 'auth.py' not found. Skipping login check.")
    pass

# ---------------------------------------------------------
# 4. GOOGLE GENERATIVE AI SETUP
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
# 5. DATA LOADING
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
        if "Date" not in df.columns:
            raise ValueError("Missing 'Date' column in CSV.")
        df["Date"] = pd.to_datetime(df["Date"])
        
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Required columns missing from CSV: {missing}")
        return df
    except Exception as e:
        return str(e)

raw_df = load_data()
if isinstance(raw_df, str):
    st.error(f"❌ Error loading data: {raw_df}")
    st.stop()

# ---------------------------------------------------------
# 6. GSHEETS CONNECTION HELPER
# ---------------------------------------------------------
def get_gsheets_conn():
    """
    Tries to get a GSheets connection using available methods:
    1. st.connections (Streamlit >= 1.28)
    2. st.experimental_connection (Older Streamlit)
    3. gspread (Manual fallback using secrets)
    """
    
    # 1) Modern Streamlit connections API
    try:
        if hasattr(st, "connections") and hasattr(st.connections, "connect"):
            if GSheetsConnection:
                return st.connections.connect("gsheets", type=GSheetsConnection)
            return st.connections.connect("gsheets")
    except Exception:
        pass

    # 2) Older experimental API
    try:
        if hasattr(st, "experimental_connection"):
            if GSheetsConnection:
                return st.experimental_connection("gsheets", type=GSheetsConnection)
            return st.experimental_connection("gsheets")
    except Exception:
        pass

    # 3) Fallback: gspread using a service account in secrets or env
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except Exception:
        raise RuntimeError(
            "No Streamlit-native connector found and gspread is not installed. "
            "Install 'gspread oauth2client' or set up streamlit-gsheets connector."
        )

    # Load service account JSON from secrets or env
    sa_info = None
    if hasattr(st, "secrets") and isinstance(st.secrets, dict):
        sa_info = st.secrets.get("gcp_service_account")
    if not sa_info:
        sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if sa_json:
            sa_info = json.loads(sa_json)

    spreadsheet_id = None
    if hasattr(st, "secrets") and isinstance(st.secrets, dict):
        gs = st.secrets.get("gsheets") or {}
        spreadsheet_id = gs.get("spreadsheet_id") if isinstance(gs, dict) else None
    if not spreadsheet_id:
        spreadsheet_id = os.getenv("GSHEETS_SPREADSHEET_ID")

    if not sa_info or not spreadsheet_id:
        raise RuntimeError(
            "Fallback gspread connector requires service account JSON in secrets['gcp_service_account'] "
            "or env GCP_SERVICE_ACCOUNT_JSON, AND spreadsheet id in secrets['gsheets']['spreadsheet_id'] or env GSHEETS_SPREADSHEET_ID."
        )

    # Build wrapper that mimics the read/update interface
    class GSpreadWrapper:
        def __init__(self, sa_info, spreadsheet_id):
            try:
                self.client = gspread.service_account_from_dict(sa_info)
            except Exception:
                scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scope)
                self.client = gspread.authorize(creds)
            self.spreadsheet_id = spreadsheet_id

        def _sheet(self, worksheet_name="Sheet1"):
            sh = self.client.open_by_key(self.spreadsheet_id)
            try:
                return sh.worksheet(worksheet_name)
            except Exception:
                return sh.sheet1

        def read(self, worksheet="Sheet1", usecols=None, ttl=None):
            ws = self._sheet(worksheet)
            rows = ws.get_all_records()
            df = pd.DataFrame(rows)
            if usecols and not df.empty:
                try:
                    cols = df.columns.tolist()
                    sel = [cols[i] for i in usecols if i < len(cols)]
                    df = df[sel]
                except Exception:
                    pass
            return df

        def update(self, worksheet="Sheet1", data=None):
            if data is None:
                raise ValueError("No data provided to update()")
            ws = self._sheet(worksheet)
            ws.clear()
            vals = [list(data.columns)] + data.fillna("").astype(str).values.tolist()
            ws.update(vals)

    return GSpreadWrapper(sa_info, spreadsheet_id)


# ---------------------------------------------------------
# 7. DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "🤖 AI Analyst", "📄 Raw Data", "📝 Feedback (Database)"])

# Sidebar filters
st.sidebar.header("Filters")
if st.sidebar.button("Log Out"):
    if "password_correct" in st.session_state:
        st.session_state["password_correct"] = False
    st.rerun() # Updated from experimental_rerun
st.sidebar.divider()

all_states = sorted(raw_df["State"].unique().tolist())
selected_state = st.sidebar.multiselect("Select State", all_states, default=all_states[:1] if all_states else [])

if not selected_state:
    filtered_df = raw_df.copy()
else:
    filtered_df = raw_df[raw_df["State"].isin(selected_state)]

daily_agg = (
    filtered_df.groupby("Date")[["Electric Vehicle (EV) Total", "Battery Electric Vehicles (BEVs)", "Plug-In Hybrid Electric Vehicles (PHEVs)"]]
    .sum()
    .reset_index()
    .sort_values("Date")
)

# --- TAB 1: DASHBOARD ---
with tab1:
    if not daily_agg.empty:
        latest = daily_agg.iloc[-1]
        col1, col2, col3 = st.columns(3)
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
                    # Attempt to find a valid model
                    chosen = "gemini-2.0-flash" # Default
                    
                    # Try listing models if possible
                    try:
                        if hasattr(genai, "list_models"):
                            preferred = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            
                            for p in preferred:
                                for a in available:
                                    if p in a:
                                        chosen = a
                                        break
                                if chosen != "gemini-2.0-flash": break
                    except Exception:
                        pass

                    # Generate content
                    model = genai.GenerativeModel(chosen)
                    response = model.generate_content(f"User asked: {user_query}. Context: EV Data.")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.info("No API key found for the AI model. Set GOOGLE_API_KEY in Streamlit secrets.")

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

                existing_data = None
                try:
                    # ttl=0 or low ttl ensures we see fresh data
                    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(3)), ttl=0)
                except Exception:
                    existing_data = pd.DataFrame(columns=["Date", "Name", "Feedback"])

                if existing_data is None or existing_data.empty:
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
                conn.update(worksheet="Sheet1", data=updated_df)

                st.success("✅ Feedback saved to Database!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
                st.info(
                    "Make sure you have set up 'connections.gsheets' in Streamlit secrets."
                )
