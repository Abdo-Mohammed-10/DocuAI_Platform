import time

import streamlit as st


def show():
    st.header("📄 Upload Document")
    client = st.session_state.client

    uploaded = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Max size: 50MB",
    )

    if uploaded:
        col1, col2 = st.columns(2)
        col1.metric("Filename", uploaded.name)
        col2.metric("Size", f"{uploaded.size / 1024:.1f} KB")

        if st.button("🚀 Upload & Process", use_container_width=True, type="primary"):
            with st.spinner("Uploading..."):
                data, status = client.upload_document(uploaded.read(), uploaded.name)

            if status in (200, 202):
                st.success("✅ Uploaded successfully! Processing started.")
                doc_id = data["id"]

                # polling loop
                progress = st.progress(0, text="Processing document...")
                for i in range(30):
                    time.sleep(2)
                    doc = client.get_document(doc_id)
                    status_val = doc.get("status", "pending")

                    if status_val == "done":
                        progress.progress(100, text="✅ Ready!")
                        st.balloons()
                        st.session_state.active_doc = doc
                        break
                    elif status_val == "failed":
                        progress.empty()
                        st.error(f"❌ Processing failed: {doc.get('error_message')}")
                        break
                    else:
                        pct = min((i + 1) * 3, 90)
                        progress.progress(pct, text=f"Processing... ({status_val})")
            else:
                st.error(data.get("detail", "Upload failed"))

    # ── Documents List ─────────────────────────────────────
    st.divider()
    st.subheader("📁 Your Documents")

    docs = client.list_documents()
    if not docs:
        st.info("No documents yet. Upload your first PDF above.")
        return

    for doc in docs:
        status_icon = {
            "done": "✅",
            "processing": "⏳",
            "pending": "🕐",
            "failed": "❌",
        }.get(doc["status"], "❓")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
            c1.write(f"**{doc['filename']}**")
            c2.write(f"{status_icon} {doc['status']}")
            c3.write(f"{doc.get('file_size', 0) // 1024} KB")
            if doc["status"] == "done":
                if c4.button("💬 Chat", key=f"chat_{doc['id']}"):
                    st.session_state.active_doc = doc
                    st.session_state.messages = []
                    st.rerun()
