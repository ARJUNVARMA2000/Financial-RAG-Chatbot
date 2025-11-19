from __future__ import annotations

import os

import requests
import streamlit as st


API_BASE = os.environ.get("FIN_RAG_API_BASE", "http://localhost:8000")


def main() -> None:
    st.title("Financial RAG Chatbot")
    st.write("Ask questions about company financials from filings, press releases, and transcripts.")

    with st.sidebar:
        st.header("Query Options")
        tickers_input = st.text_input("Tickers (comma-separated)", value="AMZN")
        period = st.text_input("Period (e.g., Q3-2025)", value="Q3-2025")
        top_k = st.slider("Top K context chunks", min_value=4, max_value=16, value=8, step=1)

    question = st.text_area("Question", value="How much money did Amazon make in the last quarter?")

    if st.button("Ask"):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        payload = {"question": question, "tickers": tickers, "period": period, "top_k": top_k}
        try:
            resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            st.error(f"Request failed: {exc}")
            return

        st.subheader("Answer")
        st.write(data.get("answer", ""))

        citations = data.get("citations", [])
        if citations:
            st.subheader("Citations")
            for idx, c in enumerate(citations, start=1):
                label = f"[{idx}] {c.get('ticker','')} {c.get('filing_type','')} {c.get('period','')}"
                st.markdown(f"**{label}**")
                st.write(
                    f"Doc ID: {c.get('doc_id','')} | Page: {c.get('page','?')} | "
                    f"Lines: {c.get('line_start','?')}–{c.get('line_end','?')}"
                )
                url = c.get("source_url")
                if url:
                    st.markdown(f"[Open source document]({url})")


if __name__ == "__main__":
    main()



