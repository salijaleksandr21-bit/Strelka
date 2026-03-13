from pydantic import BaseModel, Field

class BookResponse(BaseModel):
    id: int = Field(
        title="Идентификатор",
        description="Уникальный номер книги в базе данных",
        examples=[1, 2, 3]
    )
    name: str = Field(
        title="Наименования произведения",
        description="Каждое литературное произведение имеет свое название",
        examples=["Война и мир", "Горе от ума", "Сказка о рыбаке и рыбке"]
    )
    filename: str = Field(
        title="Путь к файлу",
        description="В формате books/filepath.txt",
        examples=["books/book1.txt", "books/book2.txt"]
    )

class OkResponse(BaseModel):
    ok: bool
