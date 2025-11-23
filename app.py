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

    div[data-tested="metric-container"] {

        background-color: #000000 !important;

        padding: 18px 20px !important;

        border-radius: 12px;

        color: white !important;

        border: 1px solid #2b2b2b !important;

    }



    /* Metric label & value color */

    div[data-tested="metric-container"] > label,

    div[data-tested="metric-container"] > div {

        color: #ffffff !important;

    }



    /* Page background (top area) */

    .stApp {

        background-color: #0b0b0b !important;

    }



    /* Tabs area background */

    .stabs [data-baseweb="tab-list"] {

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

    st.si

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
    st.si
