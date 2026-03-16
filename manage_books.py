#!/usr/bin/env python3
"""
Консольный интерфейс для управления книгами и выполнения поиска/вопросов.
Поддерживает добавление книг из JSON или текстовых файлов, выбор активной книги,
поиск фрагментов, extractive QA и гибридный режим (extractive + генерация через Llama).
"""

import sys
import os

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Добавляем путь к src для импорта модуля
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexing.book_manager import BookManager
from src.indexing import SearchEngine

def print_header(text: str):
    """Выводит заголовок с рамкой."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_books(books):
    """Выводит список книг в удобном формате."""
    if not books:
        print("📚 Нет доступных книг.")
    else:
        for i, b in enumerate(books):
            print(f"{i+1}. [{b['id']}] {b['name']}")


def main():
    manager = BookManager()

    while True:
        print_header("Управление книгами")
        print("1. Список книг")
        print("2. Добавить книгу из JSON с чанками")
        print("3. Добавить книгу из текстового файла (через processing)")
        print("4. Выбрать книгу для поиска/вопросов")
        print("5. Удалить книгу")
        print("0. Выход")

        choice = input("\nВыберите действие: ").strip()

        if choice == '1':
            books = manager.list_books()
            print_books(books)

        elif choice == '2':
            name = input("Название книги: ").strip()
            path = input("Путь к JSON с чанками: ").strip()
            try:
                book_id = manager.add_book_from_chunks(name, path)
                print(f"✅ Книга добавлена с ID: {book_id}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '3':
            name = input("Название книги: ").strip()
            file_path = input("Путь к текстовому файлу: ").strip()
            try:
                # Можно добавить параметры чанков, но пока оставим по умолчанию
                book_id = manager.add_book_from_file(name, file_path)
                print(f"✅ Книга добавлена с ID: {book_id}")
            except ImportError:
                print("❌ Модуль processing не найден. Сначала добавьте книгу из JSON (режим 2).")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '4':
            books = manager.list_books()
            if not books:
                print("❌ Нет книг. Сначала добавьте книгу.")
                continue

            print_books(books)
            try:
                idx = int(input("Введите номер книги для выбора: ").strip()) - 1
                if idx < 0 or idx >= len(books):
                    print("❌ Неверный номер.")
                    continue
                book = books[idx]
                engine = manager.get_engine(book['id'])
                print(f"✅ Выбрана книга: {book['name']} (ID: {book['id']})")

                # Подменю работы с книгой
                while True:
                    print_header(f"Работа с книгой: {book['name']}")
                    print("s. Поиск фрагментов (search)")
                    print("q. Вопрос (extractive QA)")
                    print("g. Гибридный вопрос (extractive + генерация через Llama)")
                    print("b. Вернуться к списку книг")

                    cmd = input("\nВыберите режим: ").strip().lower()

                    if cmd == 'b':
                        break
                    elif cmd == 's':
                        query = input("Запрос: ").strip()
                        if not query:
                            continue
                        try:
                            results = engine.search(query, k=5)
                            if not results:
                                print("Ничего не найдено.")
                            else:
                                for i, r in enumerate(results):
                                    print(f"\n{i+1}. [{r['book_name']} (chunk {r['chunk_id']})] "
                                          f"сходство: {r['similarity_score']:.4f}")
                                    print(r['text'][:300] + ("..." if len(r['text']) > 300 else ""))
                        except Exception as e:
                            print(f"❌ Ошибка поиска: {e}")

                    elif cmd == 'q':
                        question = input("Вопрос: ").strip()
                        if not question:
                            continue
                        try:
                            ans = engine.answer(question, k=5, score_threshold=0.1)
                            print(f"\n📌 Ответ (extractive): {ans['answer']} (уверенность: {ans['score']:.4f})")
                            print("Источники:")
                            for ch in ans['chunks']:
                                if ch.get('extracted_answer'):
                                    print(f"  - [{ch['book_name']} (chunk {ch['chunk_id']})] "
                                          f"'{ch['extracted_answer']}' (score: {ch['answer_score']:.4f})")
                        except Exception as e:
                            print(f"❌ Ошибка при ответе: {e}")

                    elif cmd == 'g':
                        question = input("Вопрос: ").strip()
                        if not question:
                            continue
                        try:
                            # Проверим, доступна ли Llama (попробуем отправить тестовый запрос)
                            # Можно добавить отдельный метод проверки, но пока просто вызовем
                            ans = engine.answer_generative(
                                question,
                                k=7,
                                threshold=0.3,
                                max_context_tokens=6000,
                                fallback_to_extractive=True
                            )
                            print(f"\n🤖 Ответ (гибридный): {ans['answer']}")
                            if 'fallback_reason' in ans:
                                print(f"(использован fallback: {ans['fallback_reason']})")
                            if ans['sources']:
                                print("Источники:")
                                for s in ans['sources']:
                                    print(f"  - [{s['book_name']} (chunk {s['chunk_id']})] "
                                          f"извлечено: '{s['extracted_answer']}' (score: {s['score']:.4f})")
                        except Exception as e:
                            print(f"❌ Ошибка при гибридном ответе: {e}")

                    else:
                        print("❌ Неизвестная команда.")

            except ValueError:
                print("❌ Введите число.")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '5':
            books = manager.list_books()
            if not books:
                print("❌ Нет книг для удаления.")
                continue
            print_books(books)
            book_id = input("Введите ID книги для удаления: ").strip()
            try:
                manager.remove_book(book_id)
                print(f"✅ Книга с ID {book_id} удалена.")
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        elif choice == '0':
            print("👋 До свидания!")
            break

        else:
            print("❌ Неверный выбор.")


if __name__ == "__main__":
    main()