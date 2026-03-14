#!/usr/bin/env python3
"""
Тестовый скрипт для модуля indexing.
Предполагается, что в директории data/ лежит файл chunks.json с тестовыми чанками.
Если файла нет, будут созданы синтетические данные.
"""

import os
import sys
import json
import tempfile
import shutil

# Добавляем путь к src для импорта модуля
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexing import SearchEngine, build_and_save_index
from src.indexing.utils import load_chunks_from_json


def create_test_chunks(tmp_dir: str) -> str:
    """Создаёт тестовый JSON с несколькими чанками и возвращает путь к нему."""
    chunks = [
        {
            "text": "Наташа Ростова была одной из любимых героинь Толстого. В романе 'Война и мир' она впервые появляется как тринадцатилетняя девочка.",
            "book_name": "war_and_peace.txt",
            "chunk_id": 1,
            "start_char": 100,
            "end_char": 300
        },
        {
            "text": "Пьер Безухов после плена женился на Наташе Ростовой. В эпилоге они счастливы, у них четверо детей.",
            "book_name": "war_and_peace.txt",
            "chunk_id": 2,
            "start_char": 1000,
            "end_char": 1200
        },
        {
            "text": "Анна Каренина бросилась под поезд. Это произошло на станции Обираловка.",
            "book_name": "anna_karenina.txt",
            "chunk_id": 1,
            "start_char": 5000,
            "end_char": 5150
        }
    ]
    json_path = os.path.join(tmp_dir, 'chunks.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    return json_path


def main():
    # Вместо создания временной директории, используем существующий файл
    chunks_path = 'путь/к/вашему/chunks_output.json'  # укажите правильный путь
    index_dir = 'data/index_real'  # папка, куда сохранится индекс

    print("=" * 60)
    print("Тестирование модуля индексации на реальных данных")
    print("=" * 60)

    # Если индекс ещё не построен
    if not os.path.exists(os.path.join(index_dir, 'faiss.index')):
        print("\n>>> Построение индекса...")
        build_and_save_index(chunks_path, index_dir, batch_size=32)
        print("Индекс построен и сохранён.")
    else:
        print("\n>>> Индекс уже существует, пропускаем построение.")

    # Загружаем поисковый движок
    print("\n>>> Загрузка SearchEngine...")
    engine = SearchEngine(index_dir)

    # Далее можно выполнять поиск и вопросы, как в оригинале
    # Например:
    query = input("Введите поисковый запрос (или нажмите Enter для пропуска): ")
    if query:
        results = engine.search(query, k=3)
        for r in results:
            print(f"{r['book_name']} (chunk {r['chunk_id']}) – сходство: {r['similarity_score']:.4f}")
            print(r['text'][:200] + "...\n")

    question = input("Введите вопрос (или нажмите Enter для пропуска): ")
    if question:
        answer_data = engine.answer(question, k=3)
        print(f"Ответ: {answer_data['answer']} (уверенность: {answer_data['score']:.4f})")
        print("Источники:")
        for ch in answer_data['chunks']:
            if ch.get('extracted_answer'):
                print(f"  - {ch['book_name']} (chunk {ch['chunk_id']}): '{ch['extracted_answer']}' (score: {ch['answer_score']:.4f})")