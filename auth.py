import streamlit as st

import json

import hashlib

import os



USER_FILE = "users.json"



# --------------------------------------

# Load User Data

# --------------------------------------

def load_users():

    if os.path.exists(USER_FILE):

        with open(USER_FILE, "r") as f:

            return json.load(f)

    return {}



def save_users(users):

    with open(USER_FILE, "w") as f:

        json.dump(users, f, indent=4)



# --------------------------------------

# Hash password

# --------------------------------------

def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()



# --------------------------------------

# Login Function

# --------------------------------------

def login_ui():

    st.title("🔐 Login")



    username = st.text_input("Username")

    password = st.text_input("Password", type="password")



    if st.button("Login"):

        users = load_users()



        if username in users and users[username] == hash_password(password):

            st.session_state["logged_in"] = True

            st.success("✅ Login successful!")

        else:

            st.error("❌ Invalid username or password")



# --------------------------------------

# Signup Function

# --------------------------------------

def signup_ui():

    st.title("🆕 Create Account")



    new_user = st.text_input("Create Username")

    new_pass = st.text_input("Create Password", type="password")

    confirm_pass = st.text_input("Confirm Password", type="password")



    if st.button("Create Account"):

        users = load_users()



        if new_user in users:

            st.error("⚠ Username already exists.")

        elif new_pass != confirm_pass:

            st.error("⚠ Passwords do not match.")

        else:

            users[new_user] = hash_password(new_pass)

            save_users(users)

            st.success("🎉 Account created! Please login now.")

            st.session_state["show_signup"] = False



# --------------------------------------

# Main Auth Page

# --------------------------------------

def auth_page():

    if "logged_in" not in st.session_state:

        st.session_state["logged_in"] = False

    if "show_signup" not in st.session_state:

        st.session_state["show_signup"] = False



    if st.session_state["logged_in"]:

        return True  # User is logged in



    if st.session_state["show_signup"]:

        signup_ui()

        st.button("⬅ Back to Login", on_click=lambda: st.session_state.update({"show_signup": False}))

    else:

        login_ui()

        st.button("Create New Account", on_click=lambda: st.session_state.update({"show_signup": True}))

    

    return False



# --------------------------------------

# Use the auth system

# --------------------------------------

if auth_page():

    st.write("### 🎉 Welcome to the EV Dashboard!")

    # Place your dashboard code here
