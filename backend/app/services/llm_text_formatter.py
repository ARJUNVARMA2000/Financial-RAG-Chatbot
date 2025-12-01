from __future__ import annotations

import os
import re
from urllib.parse import urljoin

import requests
import streamlit as st


def format_response_text(text: str) -> str:
    """Clean and format text response from LLM."""
    if not text:
        return text
    
    # Step 1: Fix numbers followed immediately by "billion/million/trillion"
    text = re.sub(r'(\d+\.?\d*)billion', r'\1 billion', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)million', r'\1 million', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+\.?\d*)trillion', r'\1 trillion', text, flags=re.IGNORECASE)
    
    # Step 2: Fix "17.4billion" -> "$17.4 billion" (add dollar sign if missing)
    text = re.sub(r'(?<!\$)(\d+\.?\d*)\s+(billion|million|trillion)', r'$\1 \2', text, flags=re.IGNORECASE)
    
    # Step 3: Fix missing spaces after periods (but not decimals)
    text = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', text)
    
    # Step 4: Fix missing spaces after punctuation
    text = re.sub(r'([.!?,;:])([A-Za-z0-9])', r'\1 \2', text)
    
    # Step 5: Fix camelCase issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Step 6: Fix missing spaces after numbers followed by letters
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    
    # Step 7: Fix common word boundaries
    word_boundaries = [
        (r'billionrelated', 'billion related'),
        (r'billionin', 'billion in'),
        (r'billionfor', 'billion for'),
        (r'billionand', 'billion and'),
        (r'millionin', 'million in'),
        (r'millionand', 'million and'),
        (r'Thisfigure', 'This figure'),
        (r'includesspecial', 'includes special'),
        (r'Withoutthese', 'Without these'),
        (r'withoutthe', 'without the'),
        (r'andthe', 'and the'),
        (r'ofthe', 'of the'),
        (r'forthe', 'for the'),
        (r'inthe', 'in the'),
    ]
    
    for pattern, replacement in word_boundaries:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Step 8-10: Fix brackets and uppercase
    text = re.sub(r'([a-z0-9])(\()', r'\1 \2', text)
    text = re.sub(r'(\))([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Z]{2,})([a-z])', r'\1 \2', text)
    
    # Step 11: Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Step 12: Fix weird spacing around decimals
    text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)
    
    # Step 13-14: Clean up newlines
    text = re.sub(r'\n +', '\n', text)
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def format_llm_response(raw_response: str) -> str:
    """
    Main function to format LLM response.
    Removes HTML, Markdown, and hidden Unicode characters.
    """
    if not raw_response:
        return raw_response
    
    # CRITICAL: Strip ANY HTML/Markdown formatting
    text = re.sub(r'<[^>]+>', '', raw_response)  # Remove HTML tags
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)        # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)          # _italic_
    
    # Remove zero-width characters
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\ufeff', '')  # BOM
    text = text.replace('\u200c', '')  # Zero-width non-joiner
    text = text.replace('\u200d', '')  # Zero-width joiner
    
    # Strip Unicode control characters
    import unicodedata
    text = ''.join(char for char in text 
                   if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
    
    # Apply formatting
    formatted = format_response_text(text)
    
    # Financial number formatting
    formatted = re.sub(r'\$\s+(\d)', r'$\1', formatted)
    formatted = re.sub(r'(\d+\.?\d*)\s*billion', r'\1 billion', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'(\d+\.?\d*)\s*million', r'\1 million', formatted, flags=re.IGNORECASE)
    
    return formatted


# ============================================================================
# REST OF YOUR STREAMLIT APP
# ============================================================================

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
        return {
            "tickers": None,
            "period": None,
            "needs_clarification": True,
            "clarification_message": f"Query parsing failed: {exc}",
        }


def handle_question(question: str, top_k: int):
    """Process a question and update session state with the answer."""
    st.session_state.messages.append({"role": "user", "content": question})
    
    status_placeholder = st.empty()
    
    with status_placeholder.status("Analyzing & Searching...", expanded=False) as status:
        status.write("Parsing query for tickers & period...")
        parsed = _parse_query(question)
        
        new_tickers = parsed.get("tickers")
        new_period = parsed.get("period")
        
        if parsed.get("needs_clarification"):
            msg = parsed.get("clarification_message", "Could not detect specific entities.")
            st.toast(f"Insight: {msg}", icon="💡")
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
            
        tickers_list = [t.strip().upper() for t in ticker_str.split(",") if t.strip()]
        payload = {
            "question": question,
            "tickers": tickers_list if tickers_list else None,
            "period": period_str if period_str.strip() else None,
            "top_k": top_k,
        }

        status.write("Retrieving documents & generating answer...")
        try:
            resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            # FORMAT THE ANSWER HERE - This is the critical fix!
            raw_answer = data.get("answer", "")
            
            # Debug output (remove after testing)
            print(f"DEBUG - Raw answer: {repr(raw_answer[:200])}")
            
            answer = format_llm_response(raw_answer)
            
            print(f"DEBUG - Formatted answer: {repr(answer[:200])}")
            
            citations = data.get("citations", [])
            status.update(label="Complete!", state="complete", expanded=False)
            
        except Exception as exc:
            status.update(label="Error", state="error", expanded=True)
            answer = f"I encountered an error: {exc}"
            citations = []

    message_data = {
        "role": "assistant",
        "content": answer,
        "citations": citations,
        "context_tickers": new_tickers if new_tickers else tickers_list,
        "context_period": new_period if new_period else period_str,
        "clarification_needed": parsed.get("needs_clarification"),
        "clarification_msg": parsed.get("clarification_message"),
    }
    st.session_state.messages.append(message_data)
    status_placeholder.empty()
