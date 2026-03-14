"""
Функции для работы с extractive QA моделью (HuggingFace Transformers).
"""

import logging
from functools import lru_cache
from typing import Tuple, Dict, Any, Optional
import numpy as np
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

logger = logging.getLogger(__name__)

# Кэш для модели и токенизатора
_QA_MODEL = None
_QA_TOKENIZER = None


@lru_cache(maxsize=1)
def get_qa_model(
    model_name: str = 'sad-bkt/rubert-finetuned-squad',
    device: Optional[str] = None
) -> Tuple[AutoModelForQuestionAnswering, AutoTokenizer]:
    """
    Загружает extractive QA модель и токенизатор. Кэширует результат.

    Args:
        model_name: Название модели на Hugging Face Hub.
        device: Устройство ('cpu', 'cuda') или None (авто).

    Returns:
        Кортеж (model, tokenizer).
    """
    global _QA_MODEL, _QA_TOKENIZER
    if _QA_MODEL is None:
        logger.info(f"Загрузка QA модели: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        if device:
            model.to(device)
        _QA_MODEL = model
        _QA_TOKENIZER = tokenizer
    return _QA_MODEL, _QA_TOKENIZER


def extract_answer(
    question: str,
    context: str,
    model: AutoModelForQuestionAnswering,
    tokenizer: AutoTokenizer,
    max_length: Optional[int] = None,
) -> Dict[str, Any]:
    # Если max_length не задан, используем model_max_length токенизатора,
    # но ограничиваем его 512 (максимум для BERT-based моделей)
    if max_length is None:
        max_length = getattr(tokenizer, 'model_max_length', 512)
        if max_length > 512:
            max_length = 512
            logger.warning(f"model_max_length превышает 512, принудительно установлено 512.")
    
    # Токенизируем вопрос и контекст вместе
    inputs = tokenizer(
        question,
        context,
        max_length=max_length,
        truncation=True,
        return_tensors='pt',
        return_offsets_mapping=True,
    )

    # Перемещаем тензоры на устройство модели
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Получаем выходы модели
    with torch.no_grad():
        outputs = model(**{k: v for k, v in inputs.items() if k != 'offset_mapping'})

    start_logits = outputs.start_logits[0].cpu().numpy()
    end_logits = outputs.end_logits[0].cpu().numpy()

    # Находим лучшие start и end позиции (в токенах)
    start_index = np.argmax(start_logits)
    end_index = np.argmax(end_logits)

    # Вычисляем уверенность
    start_probs = np.exp(start_logits - np.max(start_logits)) / np.sum(np.exp(start_logits - np.max(start_logits)))
    end_probs = np.exp(end_logits - np.max(end_logits)) / np.sum(np.exp(end_logits - np.max(end_logits)))
    score = float(start_probs[start_index] * end_probs[end_index])

    # Получаем смещения токенов для восстановления текста ответа
    offset_mapping = inputs['offset_mapping'][0].cpu().numpy()

    # Проверка на валидность позиций
    if start_index > end_index:
        return {'answer': '', 'score': 0.0, 'start': -1, 'end': -1}

    # Определяем маску токенов контекста
    token_type_ids = inputs.get('token_type_ids')
    if token_type_ids is not None:
        token_type_ids = token_type_ids[0].cpu().numpy()
        context_token_mask = (token_type_ids == 1)
    else:
        # fallback: используем поиск SEP токенов
        sep_token_id = tokenizer.sep_token_id
        input_ids = inputs['input_ids'][0].cpu().numpy()
        sep_positions = np.where(input_ids == sep_token_id)[0]
        if len(sep_positions) >= 2:
            start_context = sep_positions[1] + 1
            context_token_mask = np.zeros_like(input_ids, dtype=bool)
            context_token_mask[start_context:] = True
        else:
            context_token_mask = np.ones_like(input_ids, dtype=bool)

    # Проверяем, попадают ли start_index и end_index в контекст
    if not context_token_mask[start_index] or not context_token_mask[end_index]:
        return {'answer': '', 'score': 0.0, 'start': -1, 'end': -1}

    # Получаем символьные позиции
    start_char = offset_mapping[start_index][0]
    end_char = offset_mapping[end_index][1]

    # Извлекаем ответ
    answer_text = context[start_char:end_char]

    return {
        'answer': answer_text,
        'score': score,
        'start': int(start_char),
        'end': int(end_char),
    }