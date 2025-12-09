# 📚 Complete Setup Guide

This guide provides step-by-step instructions for setting up the Financial RAG Chatbot from scratch.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed
  - Check with: `python --version` or `python3 --version`
- **Git** installed
  - Check with: `git --version`
- **OpenAI API Key** (required)
  - Get one at: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **OpenRouter API Key** (optional, for multi-model evaluation)
  - Get one at: [openrouter.ai/keys](https://openrouter.ai/keys)

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/ARJUNVARMA2000/Financial-RAG-Chatbot.git
cd Financial-RAG-Chatbot
```

---

## Step 2: Set Up Python Environment

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv
```

### Activate Virtual Environment

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt when activated.

### Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including FastAPI, Streamlit, ChromaDB, OpenAI, and others.

---

## Step 3: Configure Environment Variables

### Create `.env` File

Copy the example environment file:

**On Windows:**
```bash
copy env.example.txt .env
```

**On macOS/Linux:**
```bash
cp env.example.txt .env
```

### Edit `.env` File

Open `.env` in your text editor and add your API keys:

```bash
# OpenAI API Configuration (required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# OpenRouter API Configuration (optional - for multi-model evaluation)
# Get your API key from https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**Important:**
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace `your_openrouter_api_key_here` with your OpenRouter API key (if using multi-model evaluation)
- The `.env` file is gitignored - your API keys will never be committed to the repository
- The backend now fails fast if `OPENAI_API_KEY` is missing, so ensure it is set before running.

---

## Step 4: Add Financial Documents

### Directory Structure

Place your financial documents in the `data/raw/<TICKER>/` directory:

```
data/raw/
├── AMZN/
│   ├── Amazon - Q3 2025.pdf
│   ├── Amazon - Q3 2025 - Conference Call Deck.pdf
│   └── Amazon - Q3 2025 - Transcript.pdf
└── MSFT/
    ├── Microsoft - Q3 2025.pdf
    └── ...
```

### Supported Formats

- **PDF files** (e.g., earnings reports, conference call decks)
- **HTML filings** (SEC filings)
- **Transcripts** (earnings call transcripts)

### Document Organization

- Create a folder for each ticker symbol (e.g., `AMZN`, `MSFT`, `AAPL`)
- Place all documents for that ticker in the corresponding folder
- Documents will be automatically parsed and indexed

---

## Step 5: Build the Vector Index

The vector index processes your documents, creates embeddings, and stores them in ChromaDB for semantic search.

### Build Index for Single Ticker

```bash
python scripts/build_index.py --ticker AMZN --period Q3-2025
```

### Build Index for Multiple Tickers

```bash
python scripts/build_index.py --ticker AMZN --ticker MSFT --period Q3-2025
```

### What Happens During Indexing

1. Documents are parsed (PDF, HTML, or text)
2. Text is chunked into smaller segments
3. Embeddings are generated using OpenAI's embedding model
4. Chunks are stored in ChromaDB with metadata (source, page, ticker, period)

**Note:** The index is stored locally in `data/indexes/chroma/` (this directory is gitignored).

---

## Step 6: Start the Backend API

Start the FastAPI backend server:

```bash
uvicorn backend.app.main:app --reload
```

The `--reload` flag enables auto-reload on code changes (useful for development).

### Verify Backend is Running

- API will be available at: `http://localhost:8000`
- Interactive API documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc`

**Keep this terminal window open** - the backend must stay running.

---

## Step 7: Launch the Frontend UI

Open a **new terminal window** (keep the backend running in the first terminal):

### Activate Virtual Environment (in new terminal)

**On Windows:**
```bash
cd path\to\Financial-RAG-Chatbot
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
cd path/to/Financial-RAG-Chatbot
source venv/bin/activate
```

### Start Streamlit

```bash
streamlit run frontend/streamlit_app.py
```

The UI will automatically open in your browser at `http://localhost:8501`

### One-command local run (optional)

Instead of starting backend and frontend separately, you can:

```bash
python scripts/run_local.py
```

This loads `.env`, starts FastAPI on port 8000 and Streamlit on port 8501, and stops both on Ctrl+C.

---

## Step 8: Verify Everything Works

### Quick Tests

1. **Backend Health Check:**
   - Visit `http://localhost:8000/health` - should return `{"status": "healthy"}`

2. **API Documentation:**
   - Visit `http://localhost:8000/docs` - should show Swagger UI

3. **Frontend UI:**
   - Visit `http://localhost:8501` - should show the chat interface

4. **Test Query:**
   - In the Streamlit UI, ask a question like: "What was AWS revenue in Q3 2025?"
   - You should receive an answer with citations

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Module not found error** | Ensure virtual environment is activated and run `pip install -r requirements.txt` |
| **API key error** | Check your `.env` file exists in the project root and `OPENAI_API_KEY` is set correctly |
| **No documents found** | Ensure documents are in `data/raw/<TICKER>/` directory and you've built the index |
| **Port 8000 already in use** | Stop other services using port 8000, or change the port: `uvicorn backend.app.main:app --port 8001` |
| **Port 8501 already in use** | Stop other Streamlit apps, or specify a different port: `streamlit run frontend/streamlit_app.py --server.port 8502` |
| **Index not found** | Run `python scripts/build_index.py --ticker <TICKER> --period <PERIOD>` to build the index |
| **Import errors** | Make sure you're in the project root directory and virtual environment is activated |

### Getting Help

- Check the [README.md](README.md) for API usage examples
- Review error messages in the terminal for specific issues
- Ensure all prerequisites are installed correctly

---

## Next Steps

Once everything is set up and running:

1. **Explore the API:** Visit `http://localhost:8000/docs` to try different endpoints
2. **Add More Documents:** Place additional financial documents in `data/raw/<TICKER>/` and rebuild the index
3. **Run Evaluation:** See the README's "Multi-Model Evaluation" section. `scripts/run_eval.py` now records per-question latency and supports `--limit N` for quick regressions.
4. **Download SEC Filings:** Use `scripts/download_filings.py` to fetch filings automatically

---

## Important Notes

- **Binary files are gitignored:** The `data/indexes/` directory (ChromaDB indexes) and `__pycache__/` directories are not tracked by git
- **Environment variables are gitignored:** Your `.env` file with API keys is never committed
- **Each user builds their own index:** Indexes are local and not shared via git
- **Keep backend running:** The FastAPI server must be running for the frontend and evaluation scripts to work

---

## Quick Reference

### Essential Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Build index
python scripts/build_index.py --ticker AMZN --period Q3-2025

# Start backend
uvicorn backend.app.main:app --reload

# Start frontend (in separate terminal)
streamlit run frontend/streamlit_app.py
```

---

For more information, see the [README.md](README.md) file.
