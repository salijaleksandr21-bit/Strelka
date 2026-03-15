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
    # Создаём временную директорию для данных
    tmp_dir = tempfile.mkdtemp(prefix="test_indexing_")
    try:
        # 1. Создаём тестовые чанки
        chunks_path = create_test_chunks(tmp_dir)
        index_dir = os.path.join(tmp_dir, 'index')

        print("=" * 60)
        print("Тестирование модуля индексации")
        print("=" * 60)

        # 2. Строим индекс (если ещё не построен)
        if not os.path.exists(os.path.join(index_dir, 'faiss.index')):
            print("\n>>> Построение индекса...")
            build_and_save_index(chunks_path, index_dir, batch_size=2)
            print("Индекс построен и сохранён.")
        else:
            print("\n>>> Индекс уже существует, пропускаем построение.")

        # 3. Загружаем поисковый движок
        print("\n>>> Загрузка SearchEngine...")
        engine = SearchEngine(index_dir)

        # 4. Тестируем поиск фрагментов
        print("\n>>> Поиск фрагментов по запросу 'Наташа Ростова' (k=2):")
        results = engine.search("Наташа Ростова", k=2)
        for i, r in enumerate(results):
            print(f"\n{i+1}. [{r['book_name']} (chunk {r['chunk_id']})] "
                  f"сходство: {r['similarity_score']:.4f}")
            print(f"   Текст: {r['text'][:100]}...")

        # 5. Тестируем ответ на вопрос
        print("\n>>> Ответ на вопрос: 'На ком женился Пьер Безухов?' (k=2)")
        answer_data = engine.answer("На ком женился Пьер Безухов?", k=2, score_threshold=0.01)
        print(f"Лучший ответ: '{answer_data['answer']}' (уверенность: {answer_data['score']:.4f})")
        print("Источники:")
        for i, ch in enumerate(answer_data['chunks']):
            print(f"  {i+1}. [{ch['book_name']} (chunk {ch['chunk_id']})] "
                  f"ответ: '{ch.get('extracted_answer', '')}' (score: {ch.get('answer_score', 0):.4f})")

        # 6. Тестируем вопрос, на который нет ответа
        print("\n>>> Ответ на вопрос: 'Сколько лет было Анне Карениной?'")
        answer_data2 = engine.answer("Сколько лет было Анне Карениной?", k=1, score_threshold=0.1)
        print(f"Ответ: '{answer_data2['answer']}' (уверенность: {answer_data2['score']:.4f})")
        if not answer_data2['answer']:
            print("   (пустой ответ, как и ожидалось)")

        print("\n" + "=" * 60)
        print("Все тесты выполнены успешно.")
        print("=" * 60)

    finally:
        # Удаляем временную директорию
        shutil.rmtree(tmp_dir)
        print(f"\nВременные файлы удалены: {tmp_dir}")


if __name__ == "__main__":
    main()