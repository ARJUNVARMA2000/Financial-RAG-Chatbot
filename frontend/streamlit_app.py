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


def _parse_query(question: str) -> dict:
    """Call the parse-query endpoint to extract entities from the question."""
    try:
        resp = requests.post(
            f"{API_BASE}/chat/parse-query",
            json={"question": question},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        # Fail silently or log, but return empty to not block chat
        return {
            "tickers": None,
            "period": None,
            "needs_clarification": True,
            "clarification_message": f"Query parsing failed: {exc}",
        }


def get_custom_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
        
        /* Global Reset & Futuristic Dark Theme */
        .stApp {
            background: radial-gradient(circle at 50% 10%, #1a1a2e 0%, #050505 100%);
            color: #E0E0E0;
            font-family: 'Outfit', sans-serif;
        }
        
        /* Minimalist Scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent; 
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1); 
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2); 
        }

        /* Input Fields (Chat Input) */
        .stChatInputContainer {
            padding-bottom: 20px;
        }
        .stChatInputContainer textarea {
            background-color: rgba(255, 255, 255, 0.05);
            color: #E0E0E0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        .stChatInputContainer textarea:focus {
            border-color: #00ADB5;
            box-shadow: 0 0 15px rgba(0, 173, 181, 0.2);
        }
        
        /* Buttons */
        .stButton button {
            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
            color: #00ADB5;
            border: 1px solid rgba(0, 173, 181, 0.3);
            border-radius: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(5px);
        }
        .stButton button:hover {
            border-color: #00ADB5;
            box-shadow: 0 0 20px rgba(0, 173, 181, 0.4);
            transform: translateY(-1px);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(10, 10, 15, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
        }
        
        /* Chat Messages */
        .stChatMessage {
            background-color: transparent;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        [data-testid="stChatMessageContent"] {
            color: #E0E0E0;
            font-family: 'Outfit', sans-serif;
            font-weight: 300;
        }
        
        /* Citations / Expander */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.03);
            color: #00ADB5;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Titles and Headers */
        h1 {
            background: linear-gradient(90deg, #00ADB5, #9D00FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            letter-spacing: -1px;
        }
        h2, h3 {
            color: #fff;
            font-weight: 600;
        }
        
        /* Links */
        a {
            color: #00ADB5 !important;
            text-decoration: none;
            transition: color 0.2s;
        }
        a:hover {
            color: #4DEEEA !important;
            text-shadow: 0 0 8px rgba(77, 238, 234, 0.4);
        }
        
        /* Status indicators */
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }

        /* Hero Section */
        .hero-container {
            text-align: center;
            padding: 4rem 2rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 2rem;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #fff 0%, #aaa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-subtitle {
            color: #888;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        /* Tags / Chips */
        .chip-container {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        .chip {
            background-color: rgba(0, 173, 181, 0.15);
            color: #00ADB5;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            border: 1px solid rgba(0, 173, 181, 0.3);
            display: inline-flex;
            align-items: center;
        }
        .chip-icon {
            margin-right: 6px;
        }
        .warning-card {
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.3);
            color: #FFC107;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            align-items: flex-start;
        }
    </style>
    """


def handle_question(question: str, top_k: int):
    """
    Process a question: parse it, search, and update session state with the answer.
    This function handles UI feedback (status) and state updates.
    """
    # 1. Display User Message (add to history immediately)
    st.session_state.messages.append({"role": "user", "content": question})
    
    # We can't render the user message *here* because this function might be called 
    # from a button callback, where `st.chat_message` context might not be ideal 
    # or would disappear on rerun. We rely on the main loop to render history.
    
    # 2. Analyze & Search
    # We use a placeholder for status since we might be inside a callback
    status_placeholder = st.empty()
    
    with status_placeholder.status("Analyzing & Searching...", expanded=False) as status:
        # Parse Query
        status.write("Parsing query for tickers & period...")
        parsed = _parse_query(question)
        
        # Update inferred values if found
        new_tickers = parsed.get("tickers")
        new_period = parsed.get("period")
        
        # Handle Clarification
        if parsed.get("needs_clarification"):
            msg = parsed.get("clarification_message", "Could not detect specific entities.")
            # Show a toast for immediate feedback without cluttering chat
            st.toast(f"Insight: {msg}", icon="💡")
            # Also write to status for record
            status.write(f"⚠️ {msg}")
        
        if new_tickers:
            ticker_str = ", ".join(new_tickers)
            st.session_state.active_tickers = ticker_str
        else:
            ticker_str = st.session_state.active_tickers

        if new_period:
            st.session_state.active_period = new_period
            period_str = new_period
        else:
            period_str = st.session_state.active_period
            
        # Prepare Payload
        tickers_list = [t.strip().upper() for t in ticker_str.split(",") if t.strip()]
        payload = {
            "question": question,
            "tickers": tickers_list if tickers_list else None,
            "period": period_str if period_str.strip() else None,
            "top_k": top_k,
        }

        # Call Chat API
        status.write("Retrieving documents & generating answer...")
        try:
            resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            answer = data.get("answer", "")
            citations = data.get("citations", [])
            
            status.update(label="Complete!", state="complete", expanded=False)
            
        except Exception as exc:
            status.update(label="Error", state="error", expanded=True)
            answer = f"I encountered an error: {exc}"
            citations = []

    # 3. Save Assistant Response (and Metadata)
    message_data = {
        "role": "assistant",
        "content": answer,
        "citations": citations,
        # Save context to display chips
        "context_tickers": new_tickers if new_tickers else tickers_list,
        "context_period": new_period if new_period else period_str,
        "clarification_needed": parsed.get("needs_clarification"),
        "clarification_msg": parsed.get("clarification_message"),
    }
    st.session_state.messages.append(message_data)

    # Clear status placeholder (optional, keeps UI clean)
    status_placeholder.empty()


def main() -> None:
    st.set_page_config(
        page_title="FinRAG Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Inject Custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "active_tickers" not in st.session_state:
        st.session_state.active_tickers = ""
    if "active_period" not in st.session_state:
        st.session_state.active_period = ""

    # Sidebar Configuration
    with st.sidebar:
        st.header("Configuration")
        
        tickers_input = st.text_input(
            "Ticker(s)",
            value=st.session_state.active_tickers,
            key="input_tickers_widget",
            placeholder="e.g., AMZN",
        )
        
        period_input = st.text_input(
            "Period",
            value=st.session_state.active_period,
            key="input_period_widget",
            placeholder="e.g., Q3-2025",
        )
        
        # Sync widget values back to active state
        if tickers_input != st.session_state.active_tickers:
            st.session_state.active_tickers = tickers_input
        if period_input != st.session_state.active_period:
            st.session_state.active_period = period_input

        st.markdown("---")
        with st.expander("Advanced Options"):
            top_k = st.slider("Top K context chunks", 4, 16, 8, 1)
            
        if st.button("Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()

    # Main Content Area
    st.title("Financial RAG Chatbot")
    
    # If chat history is empty, show Hero Section
    if not st.session_state.messages:
        st.markdown("""
            <div class="hero-container">
                <div class="hero-title">Financial Intelligence Redefined</div>
                <div class="hero-subtitle">
                    Analyze filings, transcripts, and press releases with AI-powered precision.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Ask Sample: How much money did Amazon make in Q3 2025?", use_container_width=True):
                handle_question("How much money did Amazon make in Q3 2025?", top_k)
                st.rerun()

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # If it's an assistant message, we might have metadata (chips/warnings)
            if msg["role"] == "assistant":
                # 1. Warning Card
                if msg.get("clarification_needed"):
                    st.markdown(
                        f"""
                        <div class="warning-card">
                            <span style="font-size: 1.2em; margin-right: 10px;">⚠️</span>
                            <div>
                                <strong>Clarification Needed</strong><br/>
                                {msg.get('clarification_msg', 'Could not detect entities.')}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                # 2. Context Chips
                tickers = msg.get("context_tickers")
                period = msg.get("context_period")
                if tickers or period:
                    chips_html = '<div class="chip-container">'
                    if tickers:
                        # If list, join. If string, just use.
                        t_str = ", ".join(tickers) if isinstance(tickers, list) else str(tickers)
                        chips_html += f'<span class="chip"><span class="chip-icon">🏢</span>{t_str}</span>'
                    if period:
                        chips_html += f'<span class="chip"><span class="chip-icon">📅</span>{period}</span>'
                    chips_html += '</div>'
                    st.markdown(chips_html, unsafe_allow_html=True)

            st.write(msg["content"])
            if "citations" in msg and msg["citations"]:
                with st.expander(f"📚 {len(msg['citations'])} References", expanded=False):
                    for idx, citation in enumerate(msg["citations"], start=1):
                        page_num = citation.get('page')
                        line_start = citation.get('line_start')
                        line_end = citation.get('line_end')
                        
                        # Format page display
                        if page_num:
                            page_display = f"Page {page_num}"
                        else:
                            page_display = "Page N/A"
                        
                        # Format line display
                        if line_start and line_end:
                            line_display = f"Lines {line_start}-{line_end}"
                        elif line_start:
                            line_display = f"Line {line_start}"
                        else:
                            line_display = "Lines N/A"
                        
                        ticker = citation.get('ticker', '').upper() if citation.get('ticker') else ''
                        period = citation.get('period', '')
                        filing_type = citation.get('filing_type', '')
                        doc_title = citation.get('doc_title', '')
                        relevance_score = citation.get('relevance_score')
                        
                        # Format relevance score
                        relevance_display = ""
                        if relevance_score is not None:
                            relevance_percent = int(relevance_score * 100)
                            # Color based on relevance: green for high, yellow for medium, gray for low
                            if relevance_score >= 0.7:
                                relevance_color = "#10b981"  # green
                            elif relevance_score >= 0.5:
                                relevance_color = "#f59e0b"  # yellow
                            else:
                                relevance_color = "#6b7280"  # gray
                            relevance_display = f'<span style="background: {relevance_color}20; color: {relevance_color}; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;">{relevance_percent}% match</span>'
                        
                        # Create a more visually appealing citation card
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
                            border-left: 4px solid #3b82f6;
                            padding: 1rem;
                            border-radius: 0.5rem;
                            margin-bottom: 1rem;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                                <div style="flex: 1;">
                                    <div style="display: flex; align-items: center; flex-wrap: wrap;">
                                        <strong style="font-size: 1.1rem; color: #1e40af;">[{idx}] {ticker} {period}</strong>
                                        {relevance_display}
                                    </div>
                                    <div style="font-size: 0.9rem; color: #6b7280; margin-top: 0.25rem;">
                                        {filing_type} • {page_display} • {line_display}
                                    </div>
                                    {f'<div style="font-size: 0.85rem; color: #9ca3af; margin-top: 0.25rem; font-style: italic;">{doc_title}</div>' if doc_title else ''}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons in columns
                        cols = st.columns([1, 1, 1])
                        highlight_url = citation.get("highlight_url")
                        source_url = citation.get("source_url")
                        citation_text = citation.get("text")
                        
                        if highlight_url:
                            cols[0].link_button("🔍 View in PDF", _resolve_url(highlight_url), use_container_width=True)
                        if source_url:
                            cols[1].link_button("📄 Source PDF", source_url, use_container_width=True)
                        
                        # Show text preview
                        if citation_text:
                            with cols[2].expander("👁️ Preview", expanded=False):
                                preview_text = citation_text[:300]
                                st.text(preview_text + ("..." if len(citation_text) > 300 else ""))
                        
                        st.markdown("---")

    # Chat Input
    if prompt := st.chat_input("Ask a question about financials..."):
        handle_question(prompt, top_k)
        st.rerun()

if __name__ == "__main__":
    main()
