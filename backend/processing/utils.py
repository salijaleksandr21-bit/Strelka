# вспомогательные функции (сохранение, загрузка)
import json

def save_chunks_to_json(chunks: list[dict], output_path: str) -> None:
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

def load_chunks_from_json(input_path: str) -> list[dict]:
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)