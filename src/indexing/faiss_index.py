"""
Функции для построения, сохранения, загрузки и поиска в индексе FAISS.
"""

import os
import logging
from typing import Tuple
import numpy as np
import faiss

logger = logging.getLogger(__name__)


def build_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Строит индекс FAISS типа IndexFlatIP (внутреннее произведение) для нормализованных векторов.

    Args:
        embeddings: Массив эмбеддингов формы (n_vectors, dim).

    Returns:
        Индекс FAISS с добавленными векторами.
    """
    if embeddings.size == 0:
        raise ValueError("Массив эмбеддингов пуст, нечего индексировать.")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # косинусное сходство после нормализации
    index.add(embeddings)
    logger.info(f"Построен индекс FAISS с {index.ntotal} векторами размерности {dim}.")
    return index


def save_index(index: faiss.Index, path: str) -> None:
    """
    Сохраняет индекс FAISS на диск.

    Args:
        index: Индекс FAISS.
        path: Путь для сохранения (например, 'data/index/faiss.index').
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    faiss.write_index(index, path)
    logger.info(f"Индекс сохранён в {path}")


def load_index(path: str) -> faiss.Index:
    """
    Загружает индекс FAISS с диска.

    Args:
        path: Путь к файлу индекса.

    Returns:
        Загруженный индекс.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл индекса не найден: {path}")
    index = faiss.read_index(path)
    logger.info(f"Индекс загружен из {path}, содержит {index.ntotal} векторов.")
    return index


def search(
    query_embedding: np.ndarray,
    index: faiss.Index,
    k: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Выполняет поиск k ближайших соседей для одного запроса.

    Args:
        query_embedding: Эмбеддинг запроса формы (dim,).
        index: Индекс FAISS.
        k: Количество результатов.

    Returns:
        (distances, indices) – массивы формы (k,).
    """
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)
    distances, indices = index.search(query_embedding, k)
    # Возвращаем плоские массивы для одного запроса
    return distances[0], indices[0]