from fastapi import FastAPI

from .routes import chat, health

app = FastAPI(
    title="Financial RAG Chatbot",
    description="LLM-based chatbot for answering questions about company financials with citations.",
    version="0.1.0",
)


@app.get("/")
def root() -> dict:
    return {"message": "Financial RAG Chatbot API"}


app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


