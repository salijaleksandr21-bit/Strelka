import os
import json
import shutil
from typing import List, Dict, Optional
from src.indexing.search_engine import SearchEngine
from .utils import build_and_save_index
import logging

logger = logging.getLogger(__name__)

class BookManager:
    """
    Менеджер для работы с несколькими книгами.
    Каждая книга хранится в отдельной папке с индексом и метаданными.
    """
    
    def __init__(self, books_root: str = "data/books"):
        self.books_root = books_root
        os.makedirs(books_root, exist_ok=True)
        self.registry_path = os.path.join(books_root, "books_index.json")
        self._load_registry()
    
    def _load_registry(self):
        """Загружает реестр книг из JSON."""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.books = json.load(f)
        else:
            self.books = []
    
    def _save_registry(self):
        """Сохраняет реестр книг."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.books, f, ensure_ascii=False, indent=2)
    
    def list_books(self) -> List[Dict]:
        """Возвращает список доступных книг (id, название, путь)."""
        return self.books.copy()
    
    def get_engine(self, book_id: str) -> SearchEngine:
        """
        Возвращает SearchEngine для указанной книги.
        book_id может быть как ID, так и названием папки.
        """
        # Находим книгу по ID
        book_info = next((b for b in self.books if b['id'] == book_id), None)
        if not book_info:
            raise ValueError(f"Книга с id '{book_id}' не найдена.")
        
        book_dir = os.path.join(self.books_root, book_info['path'])
        return SearchEngine(index_dir=book_dir)
    
    def add_book_from_chunks(self, book_name: str, chunks_path: str, book_id: Optional[str] = None) -> str:
        """
        Добавляет книгу из готового JSON-файла с чанками.
        
        Args:
            book_name: Название книги (для отображения).
            chunks_path: Путь к JSON с чанками (формат как у участника №1).
            book_id: Уникальный идентификатор (если не задан, генерируется из book_name).
        
        Returns:
            ID созданной книги.
        """
        if not book_id:
            book_id = book_name.lower().replace(' ', '_').replace('/', '_')
        
        # Создаём папку для книги
        book_dir = os.path.join(self.books_root, book_id)
        if os.path.exists(book_dir):
            raise FileExistsError(f"Книга с id '{book_id}' уже существует.")
        os.makedirs(book_dir)
        
        # Строим индекс
        build_and_save_index(chunks_path, book_dir)
        
        # Сохраняем информацию о книге
        book_info = {
            'id': book_id,
            'name': book_name,
            'path': book_id,
            'chunks_source': chunks_path
        }
        with open(os.path.join(book_dir, 'info.json'), 'w', encoding='utf-8') as f:
            json.dump(book_info, f, ensure_ascii=False, indent=2)
        
        # Добавляем в реестр
        self.books.append(book_info)
        self._save_registry()
        
        logger.info(f"Книга '{book_name}' (id: {book_id}) успешно добавлена.")
        return book_id
    
    def add_book_from_file(self, book_name: str, file_path: str, book_id: Optional[str] = None, chunk_size: int = 200, overlap: int = 30) -> str:
        """
        Добавляет книгу из исходного текстового файла, используя модуль processing.
        Автоматически определяет кодировку через встроенную функцию read_file.
        """
        try:
            from src.processing import split_into_chunks, read_file
        except ImportError as e:
            raise ImportError(f"Модуль processing не найден или отсутствуют необходимые функции: {e}. Сначала добавьте книгу из JSON (режим 2).")

        # Читаем текст из файла с автоматическим определением кодировки
        try:
            text = read_file(file_path)
        except Exception as e:
            raise IOError(f"Не удалось прочитать файл {file_path}: {e}")

        # Разбиваем на чанки
        chunks = split_into_chunks(text, book_name, chunk_size=chunk_size, overlap=overlap)

        # Сохраняем во временный JSON
        import tempfile
        import json
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump(chunks, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        try:
            return self.add_book_from_chunks(book_name, tmp_path, book_id)
        finally:
            os.unlink(tmp_path)
    
    def remove_book(self, book_id: str):
        """Удаляет книгу (индекс и метаданные)."""
        book_info = next((b for b in self.books if b['id'] == book_id), None)
        if not book_info:
            raise ValueError(f"Книга с id '{book_id}' не найдена.")
        
        book_dir = os.path.join(self.books_root, book_info['path'])
        shutil.rmtree(book_dir)
        self.books = [b for b in self.books if b['id'] != book_id]
        self._save_registry()
        logger.info(f"Книга '{book_info['name']}' (id: {book_id}) удалена.")