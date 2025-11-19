## Financial RAG Chatbot

LLM-based chatbot that answers questions about company financials from filings, press releases, and transcripts with line-level citations.

### Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI credentials and data paths:

```bash
OPENAI_API_KEY=your_openai_key_here
OPENAI_BASE_URL=
```

### Running the API

```bash
uvicorn backend.app.main:app --reload
```

### Indexing example documents

1. Download documents (for example MSFT and AMZN Q4-2024 earnings materials) into `data/raw/<ticker>/`.
2. Build the index:

```bash
python scripts/build_index.py --ticker MSFT --ticker AMZN --period Q4-2024
```

### Using the chatbot

- Call the FastAPI endpoint:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Among Microsoft and Amazon which company had greater cloud revenues in Q4-2024?",
    "tickers": ["MSFT", "AMZN"],
    "period": "Q4-2024",
    "top_k": 8
  }'
```

- Or run the Streamlit UI:

```bash
streamlit run frontend/streamlit_app.py
```


