import nltk
import ssl
from nltk.tokenize import PunktSentenceTokenizer

# Загрузка необходимых ресурсов NLTK 
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


def split_into_sentences(text: str) -> list[str]:
        #Разбивает текст на предложения с помощью nltk (русский язык)
    return nltk.sent_tokenize(text, language='russian')


def count_tokens(text: str) -> int:
    #Приблизительный подсчёт количества слов в тексте
    return len(text.split())


def split_into_chunks(
    text: str,
    book_name: str,
    chunk_size: int = 400,
    overlap: int = 50
) -> list[dict]:
    #разбивает текст на чанки с перекрытием, сохраняя границы предложений.
    tokenizer = PunktSentenceTokenizer()
    spans = list(tokenizer.span_tokenize(text))
    sentences = []
    for start, end in spans:
        sent_text = text[start:end]
        word_cnt = count_tokens(sent_text)
        sentences.append({
            'text': sent_text,
            'start': start,
            'end': end,
            'word_count': word_cnt
        })

    if not sentences:
        return []

    chunks = []
    chunk_id = 0
    i = 0
    n = len(sentences)

    while i < n:
        # Начинаем новый чанк
        chunk_start_idx = i
        chunk_start_char = sentences[i]['start']
        current_words = 0

        # Собираем предложения, пока не превысим chunk_size
        j = i
        while j < n and current_words + sentences[j]['word_count'] <= chunk_size:
            current_words += sentences[j]['word_count']
            j += 1

        # Если первое предложение уже больше chunk_size – разбиваем его принудительно
        if j == i:
            sent = sentences[i]
            sent_text = sent['text']
            sent_start = sent['start']

            words = sent_text.split()
            # Найдём приблизительные позиции слов внутри предложения
            word_spans = []
            pos = 0
            for w in words:
                w_start = sent_text.find(w, pos)
                if w_start == -1:
                    w_start = pos
                w_end = w_start + len(w)
                word_spans.append((w_start, w_end))
                pos = w_end

            for k in range(0, len(words), chunk_size):
                group_words = words[k:k+chunk_size]
                group_spans = word_spans[k:k+chunk_size]
                if not group_spans:
                    break
                group_start = group_spans[0][0]
                group_end = group_spans[-1][1]
                chunk_text = sent_text[group_start:group_end]
                chunks.append({
                    'text': chunk_text,
                    'book_name': book_name,
                    'chunk_id': chunk_id,
                    'start_char': sent_start + group_start,
                    'end_char': sent_start + group_end
                })
                chunk_id += 1
            i += 1
            continue

        # Нормальный чанк из целых предложений
        chunk_end_idx = j - 1
        chunk_end_char = sentences[chunk_end_idx]['end']
        chunk_text = text[chunk_start_char:chunk_end_char]

        chunks.append({
            'text': chunk_text,
            'book_name': book_name,
            'chunk_id': chunk_id,
            'start_char': chunk_start_char,
            'end_char': chunk_end_char
        })
        chunk_id += 1

        # Определяем перекрытие для следующего чанка
        overlap_sum = 0
        overlap_idx = chunk_end_idx

        while overlap_idx >= chunk_start_idx and overlap_sum + sentences[overlap_idx]['word_count'] <= overlap:
            overlap_sum += sentences[overlap_idx]['word_count']
            overlap_idx -= 1

        # Предотвращаем зацикливание, если перекрытие покрывает весь чанк
        if overlap_sum >= current_words:
            i = chunk_end_idx + 1
        elif overlap_sum == 0:
            i = chunk_end_idx + 1
        else:
            i = overlap_idx + 1

    return chunks