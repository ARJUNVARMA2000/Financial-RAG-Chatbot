import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat, documents, health

app = FastAPI(
    title="Financial RAG Chatbot",
    description="LLM-based chatbot for answering questions about company financials with citations.",
    version="0.1.0",
)

# Configure CORS - allow frontend URL from environment or default to localhost
# Railway will set FRONTEND_URL environment variable
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:8501")
allowed_origins = [
    frontend_url,
    "http://localhost:8501",  # Keep localhost for local development
    "http://127.0.0.1:8501",  # Alternative localhost
]

# Add CORS middleware to allow PDF.js to load PDFs
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Financial RAG Chatbot API"}


app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(documents.router, tags=["documents"])


