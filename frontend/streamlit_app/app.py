import streamlit as st

from frontend.streamlit_app.pages import analytics, chat, login, upload
from frontend.streamlit_app.session import init_session, is_logged_in, logout

# ── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="DocuAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session()

# ── Not logged in → show login ─────────────────────────────
if not is_logged_in():
    login.show()
    st.stop()

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 DocuAI Tools")
    st.caption(f"👤 {st.session_state.user.get('full_name', 'User')}")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📄 Upload", "💬 Chat", "📊 Analytics"],
        label_visibility="collapsed",
    )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        logout()

# ── Main Content ───────────────────────────────────────────
if page == "📄 Upload":
    upload.show()
elif page == "💬 Chat":
    chat.show()
elif page == "📊 Analytics":
    analytics.show()
