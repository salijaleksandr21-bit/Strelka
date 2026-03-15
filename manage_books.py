#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.indexing.book_manager import BookManager

def main():
    manager = BookManager()
    
    while True:
        print("\n--- Управление книгами ---")
        print("1. Список книг")
        print("2. Добавить книгу из JSON с чанками")
        print("3. Добавить книгу из текстового файла (требуется processing)")
        print("4. Выбрать книгу для поиска")
        print("5. Удалить книгу")
        print("0. Выход")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            books = manager.list_books()
            if not books:
                print("Нет доступных книг.")
            else:
                for b in books:
                    print(f"ID: {b['id']} | Название: {b['name']}")
        
        elif choice == '2':
            name = input("Название книги: ")
            path = input("Путь к JSON с чанками: ")
            try:
                book_id = manager.add_book_from_chunks(name, path)
                print(f"Книга добавлена с ID: {book_id}")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif choice == '3':
            name = input("Название книги: ")
            file_path = input("Путь к текстовому файлу: ")
            try:
                # Предполагается, что модуль processing доступен
                book_id = manager.add_book_from_file(name, file_path)
                print(f"Книга добавлена с ID: {book_id}")
            except ImportError:
                print("Модуль processing не найден. Сначала добавьте книгу из JSON.")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif choice == '4':
            books = manager.list_books()
            if not books:
                print("Нет книг. Сначала добавьте.")
                continue
            for i, b in enumerate(books):
                print(f"{i+1}. {b['name']} (id: {b['id']})")
            idx = input("Введите номер книги для поиска: ")
            try:
                book = books[int(idx)-1]
                engine = manager.get_engine(book['id'])
                print(f"Выбрана книга: {book['name']}")
                # Теперь можно использовать engine.search и engine.answer
                while True:
                    cmd = input("\nПоиск (s) / Вопрос (q) / Вернуться (b): ").lower()
                    if cmd == 'b':
                        break
                    elif cmd == 's':
                        query = input("Запрос: ")
                        results = engine.search(query, k=5)
                        for r in results:
                            print(f"\n[{r['book_name']} (chunk {r['chunk_id']})] сходство: {r['similarity_score']:.4f}")
                            print(r['text'][:200] + "...")
                    elif cmd == 'q':
                        question = input("Вопрос: ")
                        ans = engine.answer(question, k=5)
                        print(f"Ответ: {ans['answer']} (уверенность: {ans['score']:.4f})")
                        for ch in ans['chunks']:
                            if ch.get('extracted_answer'):
                                print(f"  - [{ch['book_name']}] '{ch['extracted_answer']}' (score: {ch['answer_score']:.4f})")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif choice == '5':
            book_id = input("Введите ID книги для удаления: ")
            try:
                manager.remove_book(book_id)
                print("Книга удалена.")
            except Exception as e:
                print(f"Ошибка: {e}")
        
        elif choice == '0':
            break

if __name__ == "__main__":
    main()