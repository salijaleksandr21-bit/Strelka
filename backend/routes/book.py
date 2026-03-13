from fastapi import Depends, APIRouter, UploadFile, \
    File, responses, HTTPException
from sqlalchemy import select, delete
from models import book
from database import models, driver
from uuid import uuid4


router = APIRouter(prefix="/book", tags=["Источники"])


@router.get(
    path="/library", 
    name="Библиотека материалов",
    description="Пользователь получает список всех книг.",
    response_model=list[book.BookResponse]
)
async def library_route(db: driver.AsyncSession = Depends(driver.get_db)):
    result = await db.execute(select(models.Book))
    return result.scalars().fetchall()


@router.post(
    path="/add", 
    name="Добавление книги",
    description="Пользователь добавляет книгу (название и текстовый файл)",
    response_model=book.BookResponse
)
async def create_route(
    name: str, content: UploadFile = File(...), 
    db: driver.AsyncSession = Depends(driver.get_db)):
    if content.content_type != "text/plain":
        raise HTTPException(403, detail="Прикрепляйте файлы расширения *.txt!")
    if content.size > 20 * 1024 * 1024:
        raise HTTPException(403, detail="Загружайте файл размером меньше 20 MB!")
    filename = f"books/{uuid4()}.txt"
    with open(filename, "wb") as file:
        file.write(content.file.read())
    new_book = models.Book(name=name, filename=filename)
    db.add(new_book)
    await db.commit()
    return new_book


@router.post(
    path="/download", 
    name="Скачивание книги",
    description="Пользователь выбирает какую книгу ему необходимо скачать",
    response_class=responses.FileResponse
)
async def download_route(book_id: int, db: driver.AsyncSession = Depends(driver.get_db)):
    result = await db.execute(select(models.Book).filter_by(id=book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена!")
    return responses.FileResponse(
        path=book.filename,
        filename=book.filename,
        media_type="text/plain"
    )


@router.delete(
    path="/delete", 
    name="Удаление книги",
    description="Пользователь получает список всех книг.",
    response_model=book.OkResponse
)
async def delete_route(book_id: int, db: driver.AsyncSession = Depends(driver.get_db)):
    result = await db.execute(select(models.Book).filter_by(id=book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена!")
    await db.execute(delete(models.Book).where(models.Book.id == book.id))
    await db.commit()
    return {"ok": True}
