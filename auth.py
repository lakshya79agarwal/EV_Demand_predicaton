import streamlit as st
import time

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            # Don't store the password in session state
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        # Show Login Form
        st.markdown("""
            <style>
            .stTextInput {max-width: 400px; margin: 0 auto;}
            .stButton {text-align: center; margin-top: 20px;}
            .block-container {padding-top: 5rem;}
            </style>
            """, unsafe_allow_html=True)
        
        st.title("🔒 Login Required")
        st.write("Please log in to access the EV Analytics Dashboard.")
        
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        
        if "password_correct" in st.session_state and st.session_state["password_correct"] == False:
            st.error("😕 User not known or password incorrect")
            
        return False
    else:
        # Password correct
        return True
