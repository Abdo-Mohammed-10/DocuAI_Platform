import streamlit as st

from frontend.streamlit_app.session import init_session, set_user


def show():
    init_session()
    st.title("🧠 Smart Doc Intelligence")
    st.subheader("Sign in to your account")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    # ── Login ──────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Please fill in all fields.")
                return

            client = st.session_state.client
            data, status = client.login(email, password)

            if status == 200:
                token = data["access_token"]
                # جيب بيانات الـ user
                client.token = token
                user = client.me()
                set_user(token, user)
                st.success(f"Welcome back, {user.get('full_name', email)}!")
                st.rerun()
            else:
                st.error(data.get("detail", "Login failed"))

    # ── Register ───────────────────────────────────────────
    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            r_email = st.text_input("Email", key="reg_email")
            r_pass = st.text_input("Password", type="password", key="reg_pass")
            r_pass2 = st.text_input("Confirm Password", type="password")
            submit_r = st.form_submit_button("Register", use_container_width=True)

        if submit_r:
            if r_pass != r_pass2:
                st.error("Passwords don't match.")
                return
            client = st.session_state.client
            data, status = client.register(r_email, r_pass, full_name)
            if status == 201:
                st.success("Account created! Please login.")
            else:
                st.error(data.get("detail", "Registration failed"))
