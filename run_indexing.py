#!/usr/bin/env python3
"""
Скрипт для построения индекса на реальных чанках и выполнения поиска/ответов.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.indexing import SearchEngine
from src.indexing.utils import build_and_save_index

CHUNKS_PATH = 'data/chunks_output.json'
INDEX_DIR = 'data/index_real'            # папка для индекса

def main():
    # 1. Построение индекса (если нужно)
    if not os.path.exists(os.path.join(INDEX_DIR, 'faiss.index')):
        print("Построение индекса...")
        build_and_save_index(CHUNKS_PATH, INDEX_DIR, batch_size=32)
        print("Готово.")
    else:
        print("Индекс уже существует.")

    # 2. Загружаем поисковый движок
    engine = SearchEngine(INDEX_DIR)

    # 3. Интерактивный режим
    print("\nПоисковый движок загружен. Введите 'exit' для выхода.")
    while True:
        mode = input("\nВыберите режим (1 - поиск фрагмента, 2 - вопрос, exit - выход): ").strip()
        if mode == 'exit':
            break
        if mode == '1':
            query = input("Запрос: ")
            if query:
                results = engine.search(query, k=3)
                for i, r in enumerate(results):
                    print(f"\n{i+1}. [{r['book_name']} (chunk {r['chunk_id']})] сходство: {r['similarity_score']:.4f}")
                    print(r['text'][:300] + "...")
        elif mode == '2':
            question = input("Вопрос: ")
            if question:
                ans = engine.answer(question, k=3, score_threshold=0.01)
                print(f"\nОтвет: {ans['answer']} (уверенность: {ans['score']:.4f})")
                print("Источники:")
                for ch in ans['chunks']:
                    if ch.get('extracted_answer'):
                        print(f"  - [{ch['book_name']} (chunk {ch['chunk_id']})] '{ch['extracted_answer']}' (score: {ch['answer_score']:.4f})")
        else:
            print("Неверный режим.")

if __name__ == "__main__":
    main()