from fastapi import APIRouter
from models import search
from indexing.book_manager import BookManager

router = APIRouter(prefix="/search", tags=["Поиск"])
manager = BookManager("/books")

@router.get(
    path="/", 
    name="Поиск ответа",
    description="Пользователь вводит свой вопрос, а модель ИИ выбирает определенную цитату из загруженных текстов",
    response_model=search.QuoteResponse
)
async def search_route(question: str, book_id: int):
    engine = manager.get_engine(book_id)
    quotes = [item.get("text", "") for item in engine.hybrid_search(question)]
    return {"quotes": quotes}