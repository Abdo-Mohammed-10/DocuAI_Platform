import pandas as pd
import plotly.express as px
import streamlit as st


def show():
    st.header("📊 Analytics")
    client = st.session_state.client

    # ── Overview Metrics ───────────────────────────────────
    overview = client.get_analytics()
    docs = client.list_documents()

    col1, col2, col3 = st.columns(3)
    col1.metric("📄 Total Documents", overview.get("total_documents", 0))
    col2.metric("💬 Total Messages", overview.get("total_messages", 0))
    col3.metric("✅ Ready Documents", len([d for d in docs if d["status"] == "done"]))

    st.divider()

    # ── Document Status Chart ──────────────────────────────
    if docs:
        st.subheader("Document Status Distribution")

        status_counts = {}
        for d in docs:
            s = d["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        df_status = pd.DataFrame(
            list(status_counts.items()),
            columns=["Status", "Count"],
        )

        fig = px.pie(
            df_status,
            names="Status",
            values="Count",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ── Documents Table ────────────────────────────────
        st.subheader("All Documents")
        df_docs = pd.DataFrame(docs)[["filename", "status", "file_size", "created_at"]]
        df_docs["file_size"] = (df_docs["file_size"] / 1024).round(1)
        df_docs.columns = ["Filename", "Status", "Size (KB)", "Uploaded At"]
        st.dataframe(df_docs, use_container_width=True)
    else:
        st.info("No data yet. Upload documents to see analytics.")
