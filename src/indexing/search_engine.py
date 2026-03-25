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
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class SearchEngine:

    def __init__(
        self,
        index_dir: str,
        embedding_model_name: str = 'intfloat/multilingual-e5-large',
        qa_model_name: str = 'MilyaShams/rubert-russian-qa-sberquad',
        llama_model_name: str = 'qwen2.5:7b',
        llama_temperature: float = 0.5,
        device: Optional[str] = None,
        lazy_loading: bool = True,
    ):
        self.index_dir = index_dir
        self.embedding_model_name = embedding_model_name
        self.qa_model_name = qa_model_name
        self.llama_model_name = llama_model_name
        self.llama_temperature = llama_temperature
        self.device = device
        self.lazy_loading = lazy_loading

        # Загружаем индекс и метаданные
        index_path = os.path.join(index_dir, 'faiss.index')
        metadata_path = os.path.join(index_dir, 'metadata.json')

        # Если faiss.index не существует, пробуем index.faiss
        if not os.path.exists(index_path):
            alt_index = os.path.join(index_dir, 'index.faiss')
            if os.path.exists(alt_index):
                index_path = alt_index

        # Если metadata.json не существует, пробуем metadata.pkl
        if not os.path.exists(metadata_path):
            alt_metadata = os.path.join(index_dir, 'metadata.pkl')
            if os.path.exists(alt_metadata):
                metadata_path = alt_metadata

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Индекс или метаданные не найдены в {index_dir}. Сначала выполните build_and_save_index().")

        self.index = load_index(index_path)
        print(f"Размерность индекса: {self.index.d}") 

        self.metadata = load_metadata(metadata_path)

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
        if self._qa_model is None:
            logger.info("Загрузка QA модели...")
            self._qa_model, self._qa_tokenizer = get_qa_model(self.qa_model_name, device=self.device)
        return self._qa_model, self._qa_tokenizer

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        model = self._get_embedding_model()
        # Вычисляем эмбеддинг запроса (один текст)
        dim_model = model.get_sentence_embedding_dimension()
        print(f"Размерность модели: {dim_model}")
        query_emb = compute_embeddings([query], model, normalize=True)[0] 
        distances, indices = search(query_emb, self.index, k=k)

        results = []
        for idx, dist in zip(indices, distances):
            chunk = self.metadata[idx].copy()
            chunk['similarity_score'] = float(dist)  # косинусное сходство 
            results.append(chunk)
        return results

    def answer(
        self,
        question: str,
        k: int = 5,
        score_threshold: float = 0.1,
        max_context_length: Optional[int] = None
    ) -> Dict[str, Any]:
        
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
    
    def hybrid_search(
        self,
        query: str,
        k_faiss: int = 50,
        k_final: int = 7,
        alpha: float = 0.7,
        use_reciprocal_rank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Гибридный поиск: FAISS (семантический) + BM25 (лексический).
        Возвращает список чанков с полем hybrid_score.
        """
        # 1. Получаем топ‑k_faiss от FAISS
        faiss_chunks = self.search(query, k=k_faiss)
        if not faiss_chunks:
            return []

        # 2. Готовим корпус для BM25 из этих чанков
        corpus = [chunk['text'].split() for chunk in faiss_chunks]
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.split()
        bm25_scores = list(bm25.get_scores(tokenized_query))

        # Нормализуем BM25-оценки 
        max_bm25 = max(bm25_scores) if bm25_scores else 1
        norm_bm25 = [s / max_bm25 if max_bm25 > 0 else 0 for s in bm25_scores]

        # 3. Комбинируем оценки
        combined = []
        for i, chunk in enumerate(faiss_chunks):
            faiss_score = chunk.get('similarity_score', 0.0)
            if use_reciprocal_rank:
                k_rrf = 60
                faiss_rank = i + 1
                # Ранг BM25 среди всех чанков
                sorted_indices = sorted(range(len(bm25_scores)), key=lambda x: bm25_scores[x], reverse=True)
                bm25_rank = sorted_indices.index(i) + 1 if i in sorted_indices else len(bm25_scores) + 1
                combined_score = (1 / (k_rrf + faiss_rank)) + (1 / (k_rrf + bm25_rank))
            else:
                combined_score = alpha * faiss_score + (1 - alpha) * norm_bm25[i]
            combined.append((combined_score, chunk))

        combined.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, chunk in combined[:k_final]:
            chunk_copy = chunk.copy()
            chunk_copy['hybrid_score'] = score
            results.append(chunk_copy)
        return results

    def _call_llama(self, prompt: str, max_tokens: int = 512, temperature: float = 0.3) -> Optional[str]:
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.llama_model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'num_predict': max_tokens,
                        'temperature': temperature
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
                break
        return selected

    def _is_plausible(self, answer: str, question: str) -> bool:
        """Простая эвристика для отсева мусора."""
        if len(answer) < 3:
            return False
        if answer.count('!') > 2 or answer.count('?') > 2:
            return False
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        if not q_words & a_words:
            return False
        return True
    
    def answer_generative(
        self,
        question: str,
        k: int = 5,
        alpha: float = 0.5,         
        temperature: float = 0.3,
        max_context_tokens: int = 8000
    ) -> Dict[str, Any]:
        # 1. Гибридный поиск
        chunks = self.hybrid_search(
            question,
            k_faiss=100,
            k_final=k,
            alpha=alpha,                 
            use_reciprocal_rank=False
        )
        if not chunks:
            return {'answer': 'Не удалось найти информацию.', 'sources': [], 'used_chunks': []}

        # 2. Обрезаем контекст по токенам
        contexts = self._truncate_context(chunks, max_context_tokens)

        # 3. Формируем промпт
        sources_text = "\n\n".join([
            f"[Источник {i+1}]\n{ctx['text']}"
            for i, ctx in enumerate(contexts)
        ])

        prompt = f"""Ты — эксперт по анализу художественных текстов. Ответь на вопрос, используя ТОЛЬКО информацию из предоставленных источников ниже.
        
    Источники:
    {sources_text}

    Вопрос: {question}

    Инструкции:
    - Если ответ не содержится в одном источнике, но может быть собран из нескольких — сделай это, приведи соответствующие цитаты.
    - Если ответа нет в источниках — скажи "Я не могу найти ответ на этот вопрос в предоставленных текстах".
    - Всегда указывай, из какого источника ты взял информацию (например, [Источник 1]).
    - Отвечай на русском языке.

    Ответ:"""

        # 4. Генерация через Ollama с переданной температурой
        generated = self._call_llama(prompt, max_tokens=512, temperature=temperature)

        if generated is None:
            return {
                'answer': 'Ошибка генерации ответа. Проверьте, запущен ли Ollama и загружена ли модель.',
                'sources': [],
                'used_chunks': chunks
            }

        return {
            'answer': generated,
            'sources': [],
            'used_chunks': chunks
        }