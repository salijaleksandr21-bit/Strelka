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


def save_metadata(metadata: List[Dict[str, Any]], path: str) -> None:
    """
    Сохраняет метаданные (список чанков) в файл pickle.

    Args:
        metadata: Список словарей с метаданными.
        path: Путь для сохранения (например, 'data/index/metadata.pkl').
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(metadata, f)
    logger.info(f"Метаданные сохранены в {path}")


def load_metadata(path: str) -> List[Dict[str, Any]]:
    """
    Загружает метаданные из pickle-файла.

    Args:
        path: Путь к файлу метаданных.

    Returns:
        Список чанков.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл метаданных не найден: {path}")
    with open(path, 'rb') as f:
        metadata = pickle.load(f)
    logger.info(f"Метаданные загружены из {path}, {len(metadata)} записей")
    return metadata


def build_and_save_index(
    chunks_path: str,
    index_dir: str,
    embedding_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    batch_size: int = 32,
    device: Optional[str] = None,
) -> None:
    """
    Высокоуровневая функция для построения индекса и сохранения его на диск.

    Args:
        chunks_path: Путь к JSON-файлу с чанками.
        index_dir: Директория для сохранения индекса и метаданных.
        embedding_model_name: Название модели эмбеддингов.
        batch_size: Размер батча при вычислении эмбеддингов.
        device: Устройство для модели.
    """
    # Загружаем чанки
    chunks = load_chunks_from_json(chunks_path)

    # Извлекаем тексты для эмбеддингов
    texts = [chunk['text'] for chunk in chunks]

    # Загружаем модель эмбеддингов
    model = get_embedding_model(embedding_model_name, device=device)

    # Вычисляем эмбеддинги
    embeddings = compute_embeddings(texts, model, batch_size=batch_size, normalize=True)

    # Строим индекс
    index = build_index(embeddings)

    # Сохраняем индекс и метаданные
    os.makedirs(index_dir, exist_ok=True)
    save_index(index, os.path.join(index_dir, 'faiss.index'))
    save_metadata(chunks, os.path.join(index_dir, 'metadata.pkl'))

    logger.info(f"Индексация завершена. Индекс и метаданные сохранены в {index_dir}")