import streamlit as st
import pandas as pd
import plotly.express as px
import os
import google.generativeai as genai
from dotenv import load_dotenv()

# ---------------------------------------------------------
# CUSTOM CSS FOR DARK (BLACK) METRIC BACKGROUND
# ---------------------------------------------------------
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #000000 !important;
        padding: 20px;
        border-radius: 12px;
        color: white !important;
        border: 1px solid #333;
    }
    div[data-testid="metric-container"] > label {
        color: #ffffff !important;
    }
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
""", unsafe_allow_html=True)

from streamlit_gsheets import GSheetsConnection  # NEW: Import for Database
from datetime import datetime

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
try:
    from auth import check_password
    if not check_password():
        st.stop()
except ImportError:
    st.error("❌ 'auth.py' not found.")
    st.stop()

# ---------------------------------------------------------
# 3. GOOGLE GEMINI API SETUP
# ---------------------------------------------------------
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.sidebar.error("⚠ GOOGLE_API_KEY is missing.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"API Key Error: {e}")

# ---------------------------------------------------------
# 4. DATA LOADING
# ---------------------------------------------------------
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
# 5. SIDEBAR FILTERS
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

daily_agg = filtered_df.groupby("Date")[['Electric Vehicle (EV) Total', 'Battery Electric Vehicles (BEVs)', 'Plug-In Hybrid Electric Vehicles (PHEVs)']].sum().reset_index().sort_values("Date")

# ---------------------------------------------------------
# Helper: establish a gsheets connection in a version-agnostic way
# ---------------------------------------------------------

def get_gsheets_conn():
    """Try the modern and experimental Streamlit connection APIs.
    Returns a connection object or raises the last exception.
    """
    last_exc = None
    # Preferred: modern connections API
    try:
        return st.connections.connect("gsheets", type=GSheetsConnection)
    except Exception as e:
        last_exc = e
    # Fallback: experimental API
    try:
        return st.experimental_connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        last_exc = e
    # If neither worked, re-raise
    raise last_exc

# ---------------------------------------------------------
# 6. MAIN DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ EV Demand Prediction & Analytics")

# NEW: Added "Feedback" Tab
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "🤖 AI Analyst", "📄 Raw Data", "📝 Feedback (Database)"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if not daily_agg.empty:
        latest = daily_agg.iloc[-1]
        col1, col2, col3 = st.columns(3)
        try:
            col1.metric("Total EV Demand", f"{int(latest['Electric Vehicle (EV) Total']):,}")
        except Exception:
            col1.metric("Total EV Demand", latest['Electric Vehicle (EV) Total'])
        try:
            col2.metric("Battery EVs", f"{int(latest['Battery Electric Vehicles (BEVs)']):,}")
        except Exception:
            col2.metric("Battery EVs", latest['Battery Electric Vehicles (BEVs)'])
        try:
            col3.metric("Plug-in Hybrids", f"{int(latest['Plug-In Hybrid Electric Vehicles (PHEVs)']):,}")
        except Exception:
            col3.metric("Plug-in Hybrids", latest['Plug-In Hybrid Electric Vehicles (PHEVs)'])
        
        st.subheader("Demand Trend")
        fig = px.line(daily_agg, x="Date", y="Electric Vehicle (EV) Total", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: AI ANALYST ---
with tab2:
    st.subheader("💬 Chat with your Data")
    user_query = st.chat_input("Ask about trends...")
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        if api_key:
            with st.chat_message("assistant"):
                # Keep a safe timeout / error handling around the AI client
                try:
                    # Try multiple client invocation styles to support different versions of the google.generativeai package
                    ai_text = None
                    if hasattr(genai, "GenerativeModel"):
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(f"User asked: {user_query}. Context: EV Data.")
                        ai_text = getattr(response, "text", None) or getattr(response, "output", None) or str(response)
                    elif hasattr(genai, "generate_text"):
                        # newer simpler helper
                        response = genai.generate_text(model="gemini-1.5-flash", input=f"User asked: {user_query}. Context: EV Data.")
                        ai_text = getattr(response, "text", None) or getattr(response, "output", None) or str(response)
                    else:
                        ai_text = "AI client is not supported in this environment. Check your google.generativeai package version."

                    st.write(ai_text)
                except Exception as e:
                    st.error(f"AI Error: {e}")

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
                # 1. Establish Connection
                # Use version-agnostic helper
                conn = get_gsheets_conn()
                
                # 2. Fetch Existing Data
                existing_data = None
                try:
                    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(3)), ttl=5)
                except Exception:
                    # Some connector implementations may return None or raise if the sheet is empty
                    existing_data = None

                if existing_data is None:
                    existing_data = pd.DataFrame(columns=["Date", "Name", "Feedback"])

                # 3. Create New Entry
                new_entry = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Name": name,
                    "Feedback": feedback
                }])

                # 4. Append and Update
                updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)

                st.success("✅ Feedback saved to Database!")
            except Exception as e:
                st.error(f"Error saving data: {e}")
                st.info("Make sure you have set up 'connections.gsheets' in secrets and that the streamlit-gsheets connector is installed.")
