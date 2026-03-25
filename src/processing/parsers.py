import os
import logging
from .file_reader import read_file

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from ebooklib import epub
except ImportError:
    epub = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

def extract_text_from_pdf(file_path: str) -> str:
    if PdfReader is None:
        raise ImportError("PyPDF2 не установлен. Установите pypdf.")
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def extract_text_from_epub(file_path: str) -> str:
    if epub is None:
        raise ImportError("ebooklib не установлен. Установите ebooklib.")
    book = epub.read_epub(file_path)
    texts = []
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            content = item.get_body_content()
            if content:
                try:
                    decoded = content.decode('utf-8')
                except UnicodeDecodeError:
                    decoded = content.decode('latin-1', errors='ignore')
                texts.append(decoded)
    return "\n".join(texts)

def extract_text_from_fb2(file_path: str) -> str:
    if BeautifulSoup is None:
        raise ImportError("BeautifulSoup4 не установлен. Установите beautifulsoup4.")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'xml')
    body = soup.find('body')
    if body is None:
        return ""
    texts = []
    for element in body.find_all():
        if element.name in ['p', 'title', 'epigraph', 'subtitle']:
            texts.append(element.get_text())
    return "\n".join(texts)

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.txt':
        return read_file(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.epub':
        return extract_text_from_epub(file_path)
    elif ext == '.fb2':
        return extract_text_from_fb2(file_path)
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")