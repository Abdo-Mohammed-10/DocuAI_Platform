import streamlit as st


def show():
    client = st.session_state.client
    doc = st.session_state.get("active_doc")

    st.header("💬 Chat with Document")

    docs = client.list_documents()
    done = [d for d in docs if d["status"] == "done"]

    if not done:
        st.warning("No ready documents. Upload and process a PDF first.")
        return

    options = {d["filename"]: d for d in done}
    selected_name = st.selectbox("Select document", list(options.keys()))
    doc = options[selected_name]
    st.session_state.active_doc = doc

    st.caption(f"📄 {doc['filename']}  |  ID: `{doc['id']}`")
    st.divider()

    if not st.session_state.messages:
        history = client.get_history(doc["id"])
        if history and "messages" in history:
            st.session_state.messages = history["messages"]

    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        with st.chat_message(role):
            st.write(msg["content"])

    if question := st.chat_input("Ask anything about this document..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                data, status = client.ask(doc["id"], question)

            if status == 200:
                answer = data["answer"]
                st.write(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })
            else:
                st.error(f"❌ {data.get('detail', 'Something went wrong')}")
