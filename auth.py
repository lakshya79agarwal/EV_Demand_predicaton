import streamlit as st


def check_password():
    """Returns True if the user has successfully logged in."""

    def password_entered():
        username = st.session_state.get("username", "")
        password = st.session_state.get("password", "")

        st.session_state["login_attempted"] = True

        if (
            username in st.secrets["passwords"]
            and password == st.secrets["passwords"][username]
        ):
            st.session_state["password_correct"] = True

            # Never keep the password in session state
            st.session_state.pop("password", None)
            st.session_state.pop("username", None)

        else:
            st.session_state["password_correct"] = False

    def demo_login():
        st.session_state["password_correct"] = True
        st.session_state["login_attempted"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if "login_attempted" not in st.session_state:
        st.session_state["login_attempted"] = False

    if not st.session_state["password_correct"]:

        st.markdown(
            """
            <style>
            .stTextInput {
                max-width: 400px;
                margin: 0 auto;
            }

            .block-container {
                padding-top: 5rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.title("🔒 Login Required")
        st.write(
            "Please log in to access the EV Analytics Dashboard."
        )

        st.text_input(
            "Username",
            key="username"
        )

        st.text_input(
            "Password",
            type="password",
            key="password"
        )

        st.button(
            "🔐 Login",
            on_click=password_entered
        )

        if st.session_state["login_attempted"] and not st.session_state["password_correct"]:
            st.error("😕 Username or password is incorrect.")

        st.divider()

        st.subheader("🚀 Demo Access")

        if "demo" in st.secrets:
            demo_username = st.secrets["demo"]["username"]

            st.info(
                f"Demo account: `{demo_username}`\n\n"
                "Use the button below to access the dashboard "
                "without entering a password."
            )

            st.button(
                "🚀 Demo Login",
                on_click=demo_login
            )
        else:
            st.warning(
                "Demo access is not configured in secrets.toml."
            )

        return False

    return True