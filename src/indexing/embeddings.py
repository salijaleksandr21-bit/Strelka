"""
Функции для работы с моделью эмбеддингов sentence-transformers.
"""

import logging
from functools import lru_cache
from typing import List, Optional
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Кэш для модели, чтобы не загружать повторно
_EMBEDDING_MODEL = None


@lru_cache(maxsize=1)
def get_embedding_model(
    model_name: str = 'intfloat/multilingual-e5-large',
    device: Optional[str] = None
) -> SentenceTransformer:
    """
    Загружает модель sentence-transformers. Кэширует результат.

    Args:
        model_name: Название модели на Hugging Face Hub.
        device: Устройство ('cpu', 'cuda') или None (автоопределение).

    Returns:
        Загруженная модель.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        logger.info(f"Загрузка модели эмбеддингов: {model_name}")
        _EMBEDDING_MODEL = SentenceTransformer(model_name, device=device)
    return _EMBEDDING_MODEL


def compute_embeddings(
    texts: List[str],
    model: SentenceTransformer,
    batch_size: int = 32,
    normalize: bool = True,
    show_progress: bool = True,
) -> np.ndarray:
    """
    Вычисляет эмбеддинги для списка текстов.

    Args:
        texts: Список строк.
        model: Модель sentence-transformers.
        batch_size: Размер батча.
        normalize: Если True, нормализует эмбеддинги (для косинусного сходства).
        show_progress: Отображать ли прогресс-бар.

    Returns:
        Массив numpy формы (len(texts), embedding_dim).
    """
    if not texts:
        return np.array([])

    logger.info(f"Вычисление эмбеддингов для {len(texts)} текстов...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    return embeddings