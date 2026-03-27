import os
import json
import shutil
import tempfile
from typing import List, Dict, Optional
from indexing.search_engine import SearchEngine
from .utils import build_and_save_index
import logging

from processing import extract_text, split_into_chunks

logger = logging.getLogger(__name__)

class BookManager:
    def __init__(self, books_root: str = "data/books"):
        self.books_root = books_root
        os.makedirs(books_root, exist_ok=True)
        self.registry_path = os.path.join(books_root, "books_index.json")
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.books = json.load(f)
        else:
            self.books = []

    def _save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.books, f, ensure_ascii=False, indent=2)

    def list_books(self) -> List[Dict]:
        return self.books.copy()

    def get_engine(self, book_id: str) -> SearchEngine:
        book_info = next((b for b in self.books if b['id'] == book_id), None)
        if not book_info:
            raise ValueError(f"Книга с id '{book_id}' не найдена.")
        book_dir = os.path.join(self.books_root, book_info['path'])
        return SearchEngine(index_dir=book_dir)

    def add_book_from_chunks(self, book_name: str, chunks_path: str, book_id: Optional[str] = None) -> str:
        if not book_id:
            book_id = book_name.lower().replace(' ', '_').replace('/', '_')
        book_dir = os.path.join(self.books_root, book_id)
        if os.path.exists(book_dir):
            raise FileExistsError(f"Книга с id '{book_id}' уже существует.")
        os.makedirs(book_dir)

        build_and_save_index(chunks_path, book_dir)

        book_info = {
            'id': book_id,
            'name': book_name,
            'path': book_id,
            'chunks_source': chunks_path
        }
        with open(os.path.join(book_dir, 'info.json'), 'w', encoding='utf-8') as f:
            json.dump(book_info, f, ensure_ascii=False, indent=2)

        self.books.append(book_info)
        self._save_registry()
        logger.info(f"Книга '{book_name}' (id: {book_id}) успешно добавлена.")
        return book_id

    def add_book_from_file(self, book_name: str, file_path: str,
                           book_id: Optional[str] = None,
                           chunk_size: int = 500, overlap: int = 100) -> str:
        text = extract_text(file_path)
        chunks = split_into_chunks(text, book_name, chunk_size, overlap)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False, encoding='utf-8') as tmp:
            json.dump(chunks, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        try:
            return self.add_book_from_chunks(book_name, tmp_path, book_id)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def remove_book(self, book_id: str):
        book_info = next((b for b in self.books if b['id'] == book_id), None)
        if not book_info:
            raise ValueError(f"Книга с id '{book_id}' не найдена.")
        book_dir = os.path.join(self.books_root, book_info['path'])
        shutil.rmtree(book_dir)
        self.books = [b for b in self.books if b['id'] != book_id]
        self._save_registry()
        logger.info(f"Книга '{book_info['name']}' (id: {book_id}) удалена.")