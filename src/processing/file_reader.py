# определение кодировки
import chardet

def detect_encoding(file_path: str, sample_size: int = 10240) -> str:
    with open(file_path, 'rb') as f:
        raw_data = f.read(sample_size)
    result = chardet.detect(raw_data)
    return result['encoding'] or 'utf-8'

def read_file(file_path: str) -> str:
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()