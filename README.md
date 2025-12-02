# 📊 Financial RAG Chatbot

An intelligent LLM-powered chatbot that answers questions about company financials from SEC filings, press releases, and earnings call transcripts — with **line-level citations** for full transparency.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- 🎨 **Futuristic UI** — Minimalist, dark-themed chat interface with "glassmorphism" design
- 🧠 **Smart Query Parsing** — Automatically detects tickers and time periods from your questions
- 🔍 **Semantic Search** — Retrieves relevant chunks from financial documents using vector embeddings
- 📄 **Multi-Document Support** — Handles PDFs, HTML filings, and transcripts
- 🏷️ **Line-Level Citations** — Every answer includes precise source references
- 🤖 **Multi-Model Support** — Evaluate responses across Claude, GPT, Gemini, Llama, and more
- 📊 **Built-in Evaluation Pipeline** — Compare model accuracy with Claude Opus as judge

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   FastAPI API   │────▶│   RAG Service   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
           ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
           │  Query Parser   │             │    Retriever    │             │  LLM Generator  │
           │  (Intent/Dates) │             │  (ChromaDB)     │             │  (OpenAI/Router)│
           └─────────────────┘             └─────────────────┘             └─────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Pydantic |
| **Vector Store** | ChromaDB |
| **Embeddings** | OpenAI `text-embedding-3-large` |
| **LLM** | OpenAI GPT-4.1-mini (default), OpenRouter for multi-model |
| **Document Parsing** | pdfplumber, BeautifulSoup4 |
| **Frontend** | Streamlit, Custom CSS |
| **Evaluation** | Claude Opus 4.5 as judge |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **Git** installed
- **OpenAI API Key** (required) - Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **OpenRouter API Key** (optional, for multi-model evaluation) - Get one at [openrouter.ai/keys](https://openrouter.ai/keys)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/ARJUNVARMA2000/Financial-RAG-Chatbot.git
cd Financial-RAG-Chatbot

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (you can copy from `env.example.txt`):

```bash
# On Windows:
copy env.example.txt .env

# On macOS/Linux:
cp env.example.txt .env
```

Then edit `.env` and add your API keys:

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

> **Note:** The `.env` file is gitignored for security. Never commit your API keys!

### 3. Add Documents & Build Index

Place financial documents in `data/raw/<TICKER>/`:

```
data/raw/
├── AMZN/
│   ├── Amazon - Q3 2025.pdf
│   ├── Amazon - Q3 2025 - Conference Call Deck.pdf
│   └── Amazon - Q3 2025 - Transcript.pdf
└── MSFT/
    └── ...
```

Build the vector index:

```bash
python scripts/build_index.py --all
```

### 4. Start the API Server

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Launch the Chat UI

In a **new terminal** (keep the backend running):

```bash
# Make sure your virtual environment is activated
streamlit run frontend/streamlit_app.py
```

The UI will open at `http://localhost:8501`

---

### Quick Verification

1. ✅ Backend is running: Visit `http://localhost:8000/docs` (Swagger UI)
2. ✅ Frontend is running: Visit `http://localhost:8501`
3. ✅ Test a query in the Streamlit UI

---

### Troubleshooting

| Issue | Solution |
|-------|----------|
| **Module not found** | Ensure virtual environment is activated and run `pip install -r requirements.txt` |
| **API key error** | Check your `.env` file exists and `OPENAI_API_KEY` is set correctly |
| **No documents found** | Ensure documents are in `data/raw/<TICKER>/` and you've built the index |
| **Port already in use** | Stop other services using ports 8000 or 8501, or change ports in commands |

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

---

## 🚂 Railway Deployment (FastAPI + Streamlit)

### 1. Deploy backend and frontend services

- **Connect repo to Railway**
  - Push this repo to GitHub.
  - In Railway, create a new project → **Deploy from GitHub repo**.

- **Backend service**
  - Build command: `pip install -r requirements.txt`
  - Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
  - Add environment variables (in the backend service):
    - `OPENAI_API_KEY`, `OPENAI_BASE_URL` (optional)
    - `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`
    - `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` (optional)
    - `FRONTEND_URL` (set after frontend is deployed)
  - Attach a **volume** to the backend:
    - Mount path: `/app/data`
    - This is where `data/indexes/chroma` (the Chroma database) is stored.

- **Frontend service**
  - Create a second service in the same Railway project pointing to the same repo.
  - Build command: `pip install -r requirements.txt`
  - Start command: `streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
  - Environment variables:
    - `FIN_RAG_API_BASE=https://<your-backend>.up.railway.app`

### 2. Load the pre-built Chroma index on Railway

The repository includes a pre-built Chroma index in `chroma_index.zip` so you do **not** need to upload PDFs or rebuild the index in production.

1. Open an SSH shell into the backend service (from your own machine):

   ```bash
   railway ssh --service <backend-service-name>
   ```

2. Inside the Railway shell:

   ```bash
   cd /app
   mkdir -p data/indexes
   python -c "import zipfile; z = zipfile.ZipFile('chroma_index.zip'); z.extractall('data/indexes')"
   python scripts/debug_index.py
   ```

   - `debug_index.py` should show a **non-zero** `Total chunks in collection` (≈4911) and sample chunks for tickers like `AMZN` and period `Q3-2025`.
   - The index is stored under `/app/data/indexes/chroma` on the attached volume and will persist across restarts and redeploys.

### 3. Verify the deployed app

- **Backend health:** `https://<your-backend>.up.railway.app/health`
- **API docs:** `https://<your-backend>.up.railway.app/docs`
- **Frontend UI:** `https://<your-frontend>.up.railway.app` → ask something like:
  - “What were Amazon’s total net sales in Q3 2025?”

For a more detailed, step-by-step Railway guide (including alternative ways to build the index on Railway), see `DEPLOYMENT.md`.

---

## 📡 API Usage

### Chat Endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was Amazon'\''s AWS revenue in Q3 2025?",
    "tickers": ["AMZN"],
    "period": "Q3-2025",
    "top_k": 8
  }'
```

**Response:**

```json
{
  "answer": "Amazon Web Services (AWS) generated $27.5 billion in revenue in Q3 2025...",
  "citations": [
    {
      "source": "Amazon - Q3 2025.pdf",
      "page": 5,
      "lines": "12-15",
      "text": "AWS revenue increased 19% year-over-year..."
    }
  ],
  "usage": {
    "input_tokens": 2456,
    "output_tokens": 312,
    "cost": 0.0089
  }
}
```

### Use a Specific Model

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare cloud revenue growth",
    "tickers": ["AMZN", "MSFT"],
    "period": "Q3-2025",
    "model": "claude-sonnet-4.5"
  }'
```

---

## 🧪 Multi-Model Evaluation

Evaluate RAG performance across multiple LLMs with Claude Opus as the judge.

### Available Models

| Alias | Model |
|-------|-------|
| `claude-opus-4.5` | Anthropic Claude Opus 4.5 |
| `claude-sonnet-4.5` | Anthropic Claude Sonnet 4.5 |
| `gpt-5.1` | OpenAI GPT-5.1 |
| `gemini-3-pro` | Google Gemini 3 Pro |
| `llama-4-maverick` | Meta Llama 4 Maverick |
| `kimi-k2-thinking` | Moonshot Kimi K2 |

### Run Evaluation

```bash
# Evaluate all models
python scripts/run_eval.py --csv data/eval/questions_example.csv --models all

# Evaluate specific models
python scripts/run_eval.py --csv data/eval/questions_example.csv --models claude-sonnet-4.5,gpt-5.1
```

### Evaluation CSV Format

```csv
question,expected_answer,tickers,period
"What was AWS revenue?","$27.5 billion","AMZN","Q3-2025"
"What is Azure growth rate?","29% year-over-year","MSFT","Q3-2025"
```

Results are saved to `data/eval/results/` with detailed per-question and summary CSVs.

---

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings & configuration
│   │   ├── models_registry.py   # Multi-model definitions
│   │   ├── routes/
│   │   │   ├── chat.py          # /chat endpoint
│   │   │   ├── documents.py     # Document management
│   │   │   └── health.py        # Health checks
│   │   └── services/
│   │       ├── rag_service.py   # Core RAG logic
│   │       ├── retriever.py     # Vector search
│   │       ├── citation.py      # Citation extraction
│   │       └── eval_judge.py    # LLM-as-judge
│   ├── ingestion/
│   │   ├── chunking.py          # Document chunking
│   │   ├── index_builder.py     # Index construction
│   │   └── parsers/
│   │       ├── pdf_parser.py    # PDF extraction
│   │       └── html_parser.py   # HTML/filing parser
│   └── vectorstore/
│       └── chroma_store.py      # ChromaDB wrapper
├── frontend/
│   └── streamlit_app.py         # Chat UI
├── scripts/
│   ├── build_index.py           # Build vector index
│   ├── run_eval.py              # Multi-model evaluation
│   └── download_filings.py      # Fetch SEC filings
├── data/
│   ├── raw/                     # Source documents
│   ├── indexes/                 # Vector indexes
│   └── eval/                    # Evaluation data & results
├── requirements.txt
└── README.md
```

---

## 🔧 Scripts Reference

| Script | Description |
|--------|-------------|
| `scripts/build_index.py` | Build/update the vector index from documents |
| `scripts/run_eval.py` | Run multi-model evaluation pipeline |
| `scripts/download_filings.py` | Download SEC filings for a ticker |
| `scripts/reindex_all.py` | Rebuild entire index from scratch |
| `scripts/debug_index.py` | Inspect indexed documents and chunks |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<p align="center">
  Built with ❤️ for financial analysis
</p>
