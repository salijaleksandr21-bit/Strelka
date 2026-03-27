import sys
import os
import logging
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexing.book_manager import BookManager


# Глобальные настройки по умолчанию
DEFAULT_K_SEARCH = 7          # количество результатов при поиске
DEFAULT_ALPHA = 0.5           # баланс между эмбеддингами и BM25 (0=только BM25, 1=только эмбеддинги)
DEFAULT_TEMPERATURE = 0.3     # творчество генерации (0=точный, 1=свободный)
DEFAULT_MAX_CONTEXT = 8000    # максимальное количество токенов контекста для LLM

def print_header(text: str):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_books(books: List[Dict]):
    if not books:
        print("Нет доступных книг.")
    else:
        for i, b in enumerate(books):
            print(f"{i+1}. [{b['id']}] {b['name']}")

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def show_settings(k_search, alpha, temperature, max_context):
    print_header("Текущие настройки")
    print(f"• K (количество результатов поиска/контекста): {k_search}")
    print(f"  – сколько фрагментов будет найдено и использовано при ответе.\n")
    print(f"• Alpha (баланс методов): {alpha:.2f}")
    print(f"  – 0 = только лексический поиск (BM25), 1 = только семантический (эмбеддинги).\n")
    print(f"• Temperature (творчество ответа): {temperature}")
    print(f"  – чем выше, тем более разнообразный и творческий ответ.\n")
    print(f"• Max контекст (токенов): {max_context}")
    print(f"  – максимальный объём текста, передаваемый нейросети.\n")
    print("Введите новое значение или оставьте пустым, чтобы не менять.\n")

def main():
    manager = BookManager()
    current_book = None
    current_engine = None

    # Текущие настройки (могут меняться пользователем)
    k_search = DEFAULT_K_SEARCH
    alpha = DEFAULT_ALPHA
    temperature = DEFAULT_TEMPERATURE
    max_context = DEFAULT_MAX_CONTEXT

    while True:
        if current_book is None:
            print_header("Управление книгами")
            print("1. Список книг")
            print("2. Добавить книгу из JSON")
            print("3. Добавить книгу из файла")
            print("4. Выбрать книгу")
            print("5. Удалить книгу")
            print("6. Настройки")
            print("0. Выход")
            choice = input("\nВыберите действие: ").strip()

            if choice == '1':
                books = manager.list_books()
                print_books(books)
                input("\nНажмите Enter для продолжения...")

            elif choice == '2':
                name = input("Название книги: ").strip()
                path = input("Путь к JSON с чанками: ").strip()
                try:
                    book_id = manager.add_book_from_chunks(name, path)
                    print(f"✅ Книга добавлена с ID: {book_id}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")

            elif choice == '3':
                name = input("Название книги: ").strip()
                file_path = input("Путь к файлу (txt, pdf, epub, fb2): ").strip()
                try:
                    book_id = manager.add_book_from_file(name, file_path)
                    print(f"✅ Книга добавлена с ID: {book_id}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")

            elif choice == '4':
                books = manager.list_books()
                if not books:
                    print("Нет книг. Сначала добавьте книгу.")
                    input("\nНажмите Enter для продолжения...")
                    continue
                print_books(books)
                try:
                    idx = int(input("Введите номер книги для выбора: ").strip()) - 1
                    if idx < 0 or idx >= len(books):
                        print("Неверный номер.")
                        input("\nНажмите Enter для продолжения...")
                        continue
                    current_book = books[idx]
                    current_engine = manager.get_engine(current_book['id'])
                    print(f"✅ Выбрана книга: {current_book['name']}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                    input("\nНажмите Enter для продолжения...")

            elif choice == '5':
                books = manager.list_books()
                if not books:
                    print("Нет книг для удаления.")
                    input("\nНажмите Enter для продолжения...")
                    continue
                print_books(books)
                book_id = input("Введите ID книги для удаления: ").strip()
                try:
                    manager.remove_book(book_id)
                    print(f"✅ Книга с ID {book_id} удалена.")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")

            elif choice == '6':
                show_settings(k_search, alpha, temperature, max_context)
                new_k = input(f"K ({k_search}): ").strip()
                if new_k:
                    k_search = int(new_k)
                new_alpha = input(f"Alpha ({alpha:.2f}): ").strip()
                if new_alpha:
                    alpha = float(new_alpha)
                new_temp = input(f"Temperature ({temperature}): ").strip()
                if new_temp:
                    temperature = float(new_temp)
                new_max = input(f"Max контекст ({max_context}): ").strip()
                if new_max:
                    max_context = int(new_max)
                print("✅ Настройки обновлены.")
                input("\nНажмите Enter для продолжения...")

            elif choice == '0':
                print("До свидания!")
                break

            else:
                print("Неверный выбор.")
                input("\nНажмите Enter для продолжения...")

        else:
            # Работа с выбранной книгой
            print_header(f"Работа с книгой: {current_book['name']}")
            print("1. Гибридный поиск (похожие фрагменты)")
            print("2. Гибридный ответ (генерация ответа на вопрос)")
            print("3. Настройки (для текущей книги)")
            print("4. Выбрать другую книгу")
            print("0. Вернуться в главное меню")
        

            cmd = input("\nВыберите действие: ").strip()

            if cmd == '1':
                query = input("Запрос: ").strip()
                if not query:
                    continue
                try:
                    results = current_engine.hybrid_search(
                        query,
                        k_faiss=100,
                        k_final=k_search,
                        alpha=alpha,
                        use_reciprocal_rank=False
                    )
                    if not results:
                        print("Ничего не найдено.")
                    else:
                        for i, r in enumerate(results):
                            score = r.get('hybrid_score', r.get('similarity_score', 0.0))
                            book_name = r.get('book_name', 'неизвестно')
                            chunk_id = r.get('chunk_id', '?')
                            print(f"\n{i+1}. [{book_name} (chunk {chunk_id})] оценка: {score:.4f}")
                            print(r['text'][:400] + ("..." if len(r['text']) > 400 else ""))
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")

            elif cmd == '2':
                question = input("Вопрос: ").strip()
                if not question:
                    continue
                try:
                    ans = current_engine.answer_generative(
                        question,
                        k=k_search,
                        alpha=alpha,
                        temperature=temperature,
                        max_context_tokens=max_context
                    )
                    print(f"\n🤖 Ответ:\n{ans['answer']}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                input("\nНажмите Enter для продолжения...")

            elif cmd == '3':
                # Настройки для текущей книги (можно менять параметры локально)
                show_settings(k_search, alpha, temperature, max_context)
                new_k = input(f"K ({k_search}): ").strip()
                if new_k:
                    k_search = int(new_k)
                new_alpha = input(f"Alpha ({alpha:.2f}): ").strip()
                if new_alpha:
                    alpha = float(new_alpha)
                new_temp = input(f"Temperature ({temperature}): ").strip()
                if new_temp:
                    temperature = float(new_temp)
                new_max = input(f"Max контекст ({max_context}): ").strip()
                if new_max:
                    max_context = int(new_max)
                print("✅ Настройки обновлены.")
                input("\nНажмите Enter для продолжения...")

            elif cmd == '4':
                books = manager.list_books()
                if not books:
                    print("Нет книг. Сначала добавьте книгу.")
                    input("\nНажмите Enter для продолжения...")
                    continue
                print_books(books)
                try:
                    idx = int(input("Введите номер книги для выбора: ").strip()) - 1
                    if idx < 0 or idx >= len(books):
                        print("Неверный номер.")
                        input("\nНажмите Enter для продолжения...")
                        continue
                    current_book = books[idx]
                    current_engine = manager.get_engine(current_book['id'])
                    print(f"✅ Выбрана книга: {current_book['name']}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                    input("\nНажмите Enter для продолжения...")


            elif cmd == '0':
                current_book = None
                current_engine = None
                continue

            else:
                print("Неверный выбор.")
                input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    clear_screen()
    main()