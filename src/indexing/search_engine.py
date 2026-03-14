"""
Класс SearchEngine, объединяющий все компоненты для удобного использования в приложении.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from .embeddings import get_embedding_model, compute_embeddings
from .faiss_index import load_index, search
from .qa_model import get_qa_model, extract_answer
from .utils import load_metadata

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Поисковый движок, основанный на FAISS и extractive QA.
    Позволяет искать похожие чанки и отвечать на вопросы по тексту.
    """

    def __init__(
        self,
        index_dir: str,
        embedding_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        qa_model_name: str = 'DeepPavlov/rubert-base-cased-squad',
        device: Optional[str] = None,
        lazy_loading: bool = True,
    ):
        """
        Инициализация SearchEngine.

        Args:
            index_dir: Директория, где лежат faiss.index и metadata.pkl.
            embedding_model_name: Название модели эмбеддингов.
            qa_model_name: Название extractive QA модели.
            device: Устройство для моделей ('cpu', 'cuda') или None (авто).
            lazy_loading: Если True, модели загружаются только при первом обращении.
        """
        self.index_dir = index_dir
        self.embedding_model_name = embedding_model_name
        self.qa_model_name = qa_model_name
        self.device = device
        self.lazy_loading = lazy_loading

        # Загружаем индекс и метаданные сразу
        index_path = os.path.join(index_dir, 'faiss.index')
        metadata_path = os.path.join(index_dir, 'metadata.pkl')
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Индекс или метаданные не найдены в {index_dir}. Сначала выполните build_and_save_index().")
        self.index = load_index(index_path)
        self.metadata = load_metadata(metadata_path)

        # Модели будут загружены по требованию
        self._embedding_model = None
        self._qa_model = None
        self._qa_tokenizer = None

    def _get_embedding_model(self):
        """Ленивая загрузка модели эмбеддингов."""
        if self._embedding_model is None:
            logger.info("Загрузка модели эмбеддингов...")
            self._embedding_model = get_embedding_model(self.embedding_model_name, device=self.device)
        return self._embedding_model

    def _get_qa_model(self):
        """Ленивая загрузка QA модели и токенизатора."""
        if self._qa_model is None:
            logger.info("Загрузка QA модели...")
            self._qa_model, self._qa_tokenizer = get_qa_model(self.qa_model_name, device=self.device)
        return self._qa_model, self._qa_tokenizer

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск k наиболее релевантных чанков по текстовому запросу.

        Args:
            query: Текстовый запрос.
            k: Количество результатов.

        Returns:
            Список чанков (словарей с метаданными), отсортированный по релевантности.
        """
        model = self._get_embedding_model()
        # Вычисляем эмбеддинг запроса (один текст)
        query_emb = compute_embeddings([query], model, normalize=True)[0]  # shape: (dim,)
        distances, indices = search(query_emb, self.index, k=k)

        results = []
        for idx, dist in zip(indices, distances):
            chunk = self.metadata[idx].copy()
            chunk['similarity_score'] = float(dist)  # косинусное сходство (нормализовано)
            results.append(chunk)
        return results

    def answer(
        self,
        question: str,
        k: int = 5,
        score_threshold: float = 0.1,
        max_context_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ответить на вопрос, используя extractive QA по найденным чанкам.

        Args:
            question: Вопрос.
            k: Количество чанков для рассмотрения.
            score_threshold: Минимальная уверенность ответа (если ниже, ответ считается пустым).
            max_context_length: Максимальная длина контекста в токенах (обрезать, если превышает).
                                 Если None, используется максимальная длина модели.

        Returns:
            Словарь с полями:
                'answer': извлечённый текст (или пустая строка).
                'score': уверенность лучшего ответа.
                'chunks': список использованных чанков (с метаданными и scores ответов).
                'best_chunk': индекс лучшего чанка (или None).
        """
        # Сначала ищем релевантные чанки
        chunks = self.search(question, k=k)

        if not chunks:
            return {'answer': '', 'score': 0.0, 'chunks': [], 'best_chunk': None}

        model, tokenizer = self._get_qa_model()

        best_answer = ''
        best_score = 0.0
        best_chunk_idx = -1
        enriched_chunks = []

        for i, chunk in enumerate(chunks):
            context = chunk['text']
            # Извлекаем ответ
            answer_data = extract_answer(
                question, context, model, tokenizer,
                max_length=max_context_length
            )
            ans = answer_data['answer']
            score = answer_data['score']

            # Сохраняем результат для чанка
            chunk_with_answer = chunk.copy()
            chunk_with_answer['extracted_answer'] = ans
            chunk_with_answer['answer_score'] = score
            enriched_chunks.append(chunk_with_answer)

            # Обновляем лучший ответ
            if score > best_score:
                best_score = score
                best_answer = ans
                best_chunk_idx = i

        # Применяем порог
        if best_score < score_threshold:
            best_answer = ''
            best_score = 0.0

        return {
            'answer': best_answer,
            'score': best_score,
            'chunks': enriched_chunks,
            'best_chunk': best_chunk_idx if best_chunk_idx >= 0 else None
        }