import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="API Diagnostics")
st.title("🛠️ Google Gemini API Diagnostics")

# 1. Get the API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try getting it from Streamlit secrets if env var fails
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

# 2. Check Key Status
if not api_key:
    st.error("❌ API Key NOT Found! Check your Render Environment Variables.")
    st.stop()
else:
    st.success(f"✅ API Key Found (starts with: {api_key[:5]}...)")

# 3. Configure Library
try:
    genai.configure(api_key=api_key)
    st.write(f"**Library Version:** `google-generativeai` (Check requirements.txt if old)")
except Exception as e:
    st.error(f"Configuration Failed: {e}")
    st.stop()

# 4. List ALL Available Models
st.subheader("🔍 Available Models for this Key")
st.write("Attempting to fetch model list from Google...")

try:
    valid_models = []
    for m in genai.list_models():
        # We only care about models that can generate content (chat)
        if 'generateContent' in m.supported_generation_methods:
            valid_models.append(m.name)
            st.code(m.name)  # Print each valid model name
    
    if not valid_models:
        st.error("❌ No chat models found! Your API key might be invalid or has no access.")
    else:
        st.success(f"Found {len(valid_models)} working models!")
        st.info(f"👉 **Recommended Fix:** Update your code to use: `{valid_models[0]}`")

except Exception as e:
    st.error(f"❌ Critical Error fetching models: {e}")
    st.write("Common causes:")
    st.write("1. The API Key is for 'Vertex AI' (Google Cloud) instead of 'AI Studio'.")
    st.write("2. The library version is too old.")
