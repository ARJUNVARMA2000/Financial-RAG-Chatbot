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

### 1. Clone & Setup Environment

```bash
git clone https://github.com/yourusername/financial-rag-chatbot.git
cd financial-rag-chatbot

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

Create a `.env` file in the project root:

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
python scripts/build_index.py --ticker AMZN --period Q3-2025
```

### 4. Start the API Server

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Launch the Chat UI

```bash
streamlit run frontend/streamlit_app.py
```

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
| `gpt-5.1-codex` | OpenAI GPT-5.1 Codex |
| `gemini-3-pro` | Google Gemini 3 Pro |
| `llama-4-maverick` | Meta Llama 4 Maverick |
| `qwen-max` | Alibaba Qwen Max |
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
