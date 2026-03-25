#!/usr/bin/env python3
import os
import sys

def find_project_root(marker='src'):
    current = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.isdir(os.path.join(current, marker)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent

root = find_project_root()
if root is None:
    print("Не удалось найти корень проекта (папку src).", file=sys.stderr)
    sys.exit(1)
sys.path.insert(0, root)

from src.processing.file_reader import read_file
from src.processing.chunker import split_into_chunks
from src.processing.utils import save_chunks_to_json

def main():
    file_path = os.path.join('data', '.txt')
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден. Создайте его для тестирования.")
        return

    text = read_file(file_path)
    print(f"Прочитано {len(text)} символов.")

    chunks = split_into_chunks(text, book_name=os.path.basename(file_path))
    print(f"Создано чанков: {len(chunks)}")

    if chunks:
        print("\nПример первого чанка:")
        print(chunks[0]['text'][:200] + "...")

    output_json = os.path.join('data', 'chunks_output.json')
    save_chunks_to_json(chunks, output_json)
    print(f"\nЧанки сохранены в {output_json}")

if __name__ == '__main__':
    main()