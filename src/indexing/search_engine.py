"""
Класс SearchEngine, объединяющий все компоненты для удобного использования в приложении.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import requests
import json

from .embeddings import get_embedding_model, compute_embeddings
from .faiss_index import load_index, search
from .qa_model import get_qa_model, extract_answer
from .utils import load_metadata

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Поисковый движок, основанный на FAISS и extractive QA.
    Позволяет искать похожие чанки и отвечать на вопросы по тексту.
    Поддерживает гибридный режим с генерацией через Llama (локально через Ollama).
    """

    def __init__(
        self,
        index_dir: str,
        embedding_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        qa_model_name: str = 'sad-bkt/rubert-finetuned-squad',
        llama_model_name: str = 'llama3.1:8b-instruct-q6_K',
        llama_temperature: float = 0.5,
        device: Optional[str] = None,
        lazy_loading: bool = True,
    ):
        """
        Инициализация SearchEngine.

        Args:
            index_dir: Директория, где лежат faiss.index и metadata.pkl.
            embedding_model_name: Название модели эмбеддингов.
            qa_model_name: Название extractive QA модели.
            llama_model_name: Название модели Llama в Ollama (например, 'llama3.1:8b-instruct-q6_K').
            llama_temperature: Температура генерации для Llama (0.0 – детерминированно, выше – креативнее).
            device: Устройство для моделей ('cpu', 'cuda') или None (авто).
            lazy_loading: Если True, модели загружаются только при первом обращении.
        """
        self.index_dir = index_dir
        self.embedding_model_name = embedding_model_name
        self.qa_model_name = qa_model_name
        self.llama_model_name = llama_model_name
        self.llama_temperature = llama_temperature
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

    def _call_llama(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """
        Отправляет запрос к локальному серверу Ollama и возвращает ответ.
        В случае ошибки возвращает None.
        """
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.llama_model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'num_predict': max_tokens,
                        'temperature': self.llama_temperature
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()['response'].strip()
        except Exception as e:
            logger.error(f"Ошибка при вызове Llama: {e}")
            return None

    def _truncate_context(self, contexts: List[Dict], max_tokens: int) -> List[Dict]:
        """
        Обрезает список контекстов так, чтобы суммарное примерное число токенов
        не превышало max_tokens. Используется эвристика 1 токен ≈ 4 символа.
        """
        avg_chars_per_token = 4
        max_chars = max_tokens * avg_chars_per_token
        total_chars = 0
        selected = []
        for ctx in contexts:
            text_len = len(ctx['text'])
            if total_chars + text_len <= max_chars:
                selected.append(ctx)
                total_chars += text_len
            else:
                # Можно попробовать обрезать последний, но это сложнее; пока просто остановимся
                break
        return selected

    def _is_plausible(self, answer: str, question: str) -> bool:
        """Простая эвристика для отсева мусора."""
        if len(answer) < 3:
            return False
        if answer.count('!') > 2 or answer.count('?') > 2:
            return False
        # Хотя бы одно слово из вопроса должно присутствовать в ответе (грубо)
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        if not q_words & a_words:
            return False
        return True

    def answer_generative(
        self,
        question: str,
        k: int = 7,
        threshold: float = 0.3,
        max_context_tokens: int = 6000,
        fallback_to_extractive: bool = True
    ) -> Dict[str, Any]:
        """
        Гибридный метод: extractive -> фильтр -> генерация через Llama.
        Возвращает ответ и использованные источники.

        Args:
            question: Вопрос.
            k: Количество чанков для поиска.
            threshold: Минимальный score extractive ответа для включения в контекст.
            max_context_tokens: Максимальное примерное число токенов контекста для Llama.
            fallback_to_extractive: Если True, при отсутствии валидных контекстов или ошибке Llama
                                    возвращается лучший extractive ответ (через метод answer).

        Returns:
            Словарь с полями:
                'answer': сгенерированный ответ (строка).
                'sources': список отобранных источников с извлечёнными ответами.
                'used_chunks': все найденные чанки (до фильтрации).
                'fallback_reason' (опционально): причина использования fallback.
        """
        # 1. Поиск чанков
        chunks = self.search(question, k=k)

        # 2. Извлечение и фильтрация ответов extractive моделью
        model, tokenizer = self._get_qa_model()
        valid_contexts = []

        for chunk in chunks:
            ans_data = extract_answer(question, chunk['text'], model, tokenizer)
            if ans_data['score'] >= threshold and self._is_plausible(ans_data['answer'], question):
                valid_contexts.append({
                    'text': chunk['text'],
                    'extracted_answer': ans_data['answer'],
                    'score': ans_data['score'],
                    'book_name': chunk['book_name'],
                    'chunk_id': chunk['chunk_id']
                })

        # 3. Если нет подходящих контекстов – fallback или возврат сообщения
        if not valid_contexts:
            if fallback_to_extractive:
                fallback = self.answer(question, k=k, score_threshold=threshold)
                return {
                    'answer': fallback['answer'],
                    'sources': [],
                    'used_chunks': chunks,
                    'fallback_reason': 'no_valid_contexts'
                }
            else:
                return {
                    'answer': 'Не удалось найти достоверную информацию в тексте.',
                    'sources': [],
                    'used_chunks': chunks
                }

        # 4. Обрезаем контекст по токенам
        valid_contexts = self._truncate_context(valid_contexts, max_context_tokens)

        # 5. Формирование промпта для Llama
        sources_text = "\n\n".join([
            f"[Источник {i+1} из книги '{ctx['book_name']}']\n{ctx['text']}"
            for i, ctx in enumerate(valid_contexts)
        ])

        prompt = f"""Ты — эксперт по анализу художественных текстов. Ответь на вопрос, используя ТОЛЬКО информацию из предоставленных источников ниже. Не добавляй ничего от себя.

Источники:
{sources_text}

Вопрос: {question}

Инструкции:
- Если источники содержат ответ — дай точный, развёрнутый ответ, основанный на них.
- Если ответа нет в источниках — скажи "Я не могу найти ответ на этот вопрос в предоставленных текстах".
- Всегда указывай, из какого источника ты взял информацию (например, [Источник 1]).
- Не придумывай факты и не используй внешние знания.

Ответ:"""

        # 6. Генерация через Llama
        generated_answer = self._call_llama(prompt)

        # 7. Обработка ошибки генерации
        if generated_answer is None:
            if fallback_to_extractive:
                fallback = self.answer(question, k=k, score_threshold=threshold)
                return {
                    'answer': fallback['answer'],
                    'sources': valid_contexts,
                    'used_chunks': chunks,
                    'fallback_reason': 'llama_error'
                }
            else:
                return {
                    'answer': '[Ошибка генерации ответа]',
                    'sources': valid_contexts,
                    'used_chunks': chunks
                }

        return {
            'answer': generated_answer,
            'sources': valid_contexts,
            'used_chunks': chunks
        }