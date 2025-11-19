from fastapi import APIRouter, Depends

from ..schemas import ChatRequest, ChatResponse
from ..services.rag_service import RAGService, get_rag_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    return rag_service.answer(request)



