"""
Вспомогательные функции для загрузки чанков, сохранения метаданных и высокоуровневой индексации.
"""

import json
import pickle
import os
import logging
from typing import List, Dict, Any, Optional

from .embeddings import get_embedding_model, compute_embeddings
from .faiss_index import build_index, save_index

logger = logging.getLogger(__name__)


def load_chunks_from_json(json_path: str) -> List[Dict[str, Any]]:
    """
    Загружает список чанков из JSON-файла.

    Args:
        json_path: Путь к JSON-файлу с чанками.

    Returns:
        Список словарей, каждый с ключами 'text', 'book_name', 'chunk_id', 'start_char', 'end_char'.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Файл чанков не найден: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    logger.info(f"Загружено {len(chunks)} чанков из {json_path}")
    return chunks


def save_metadata(metadata: list, path: str):
    """Сохраняет метаданные в JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_metadata(path: str) -> list:
    """
    Загружает метаданные из файла (JSON or pickle).
    Сначала пробует pickle, затем JSON.
    """
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except (pickle.UnpicklingError, EOFError, AttributeError, ImportError):
        # Если не pickle, пробуем JSON
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


def build_and_save_index(chunks_path: str, output_dir: str, embedding_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', batch_size: int = 32):
    """Строит индекс FAISS для чанков и сохраняет в output_dir.
    Сохраняет индекс как faiss.index и метаданные как metadata.json.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Загружаем чанки
    chunks = load_chunks_from_json(chunks_path)
    texts = [chunk['text'] for chunk in chunks]

    # Вычисляем эмбеддинги
    model = get_embedding_model(embedding_model_name)
    embeddings = compute_embeddings(texts, model, batch_size=batch_size, normalize=True)

    # Строим индекс FAISS
    index = build_index(embeddings)
    save_index(index, os.path.join(output_dir, 'faiss.index'))

    # Сохраняем метаданные в JSON (только нужные поля)
    metadata = [{"text": c["text"], "book_name": c["book_name"], "chunk_id": c["chunk_id"]} for c in chunks]
    save_metadata(metadata, os.path.join(output_dir, 'metadata.json'))

    logger.info(f"Индекс и метаданные сохранены в {output_dir}")