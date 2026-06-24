import streamlit as st

from frontend.streamlit_app.api_client import APIClient


def init_session():
    """initialize session state variables"""
    defaults = {
        "token": "",
        "user": None,
        "client": APIClient(),
        "active_doc": None,
        "messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_logged_in() -> bool:
    return bool(st.session_state.get("token"))


def set_user(token: str, user: dict):
    st.session_state.token = token
    st.session_state.user = user
    st.session_state.client = APIClient(token=token)


def logout():
    for k in ["token", "user", "client", "active_doc", "messages"]:
        st.session_state.pop(k, None)
    st.rerun()
