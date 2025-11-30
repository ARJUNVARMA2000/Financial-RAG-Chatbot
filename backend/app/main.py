from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat, documents, health

app = FastAPI(
    title="Financial RAG Chatbot",
    description="LLM-based chatbot for answering questions about company financials with citations.",
    version="0.1.0",
)

# Add CORS middleware to allow PDF.js to load PDFs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
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


