from __future__ import annotations

import os
from urllib.parse import urljoin

import requests
import streamlit as st


API_BASE = os.environ.get("FIN_RAG_API_BASE", "http://localhost:8000")


def _resolve_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    base = API_BASE.rstrip("/") + "/"
    return urljoin(base, path_or_url.lstrip("/"))


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
            for idx, citation in enumerate(citations, start=1):
                label = f"[{idx}] {citation.get('ticker','')} {citation.get('filing_type','')} {citation.get('period','')}"
                st.markdown(f"**{label}**")
                st.write(
                    f"Doc ID: {citation.get('doc_id','')} | Page: {citation.get('page','?')} | "
                    f"Lines: {citation.get('line_start','?')} - {citation.get('line_end','?')}"
                )
                highlight_url = citation.get("highlight_url")
                if highlight_url:
                    st.link_button("Open highlighted PDF", _resolve_url(highlight_url), type="primary")
                source_url = citation.get("source_url")
                if source_url:
                    st.markdown(f"[Open source document]({source_url})")


if __name__ == "__main__":
    main()
