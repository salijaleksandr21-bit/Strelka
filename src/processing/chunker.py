import re
from typing import List, Dict

def split_into_chunks(text: str, book_name: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """
    Разбивает текст на чанки с перекрытием, стараясь не разрывать предложения.
    Возвращает список словарей с полями:
        text, book_name, chunk_id, start_char, end_char
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_len = 0
    chunk_id = 0
    start_char = 0

    for sentence in sentences:
        sent_len = len(sentence)
        if current_len + sent_len > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            end_char = start_char + len(chunk_text)
            chunks.append({
                'text': chunk_text,
                'book_name': book_name,
                'chunk_id': chunk_id,
                'start_char': start_char,
                'end_char': end_char
            })
            chunk_id += 1
            overlap_text = chunk_text[-overlap:] if overlap > 0 else ''
            overlap_sentences = re.findall(r'[^.!?]+[.!?]', overlap_text)
            if overlap_sentences:
                current_chunk = overlap_sentences
                current_len = sum(len(s) for s in current_chunk)
                start_char = max(0, end_char - overlap)
            else:
                current_chunk = []
                current_len = 0
                start_char = end_char

        current_chunk.append(sentence)
        current_len += sent_len

    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        end_char = start_char + len(chunk_text)
        chunks.append({
            'text': chunk_text,
            'book_name': book_name,
            'chunk_id': chunk_id,
            'start_char': start_char,
            'end_char': end_char
        })
    return chunks