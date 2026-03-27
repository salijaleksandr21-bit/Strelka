# Международный конкурс "Технострелка". Направление: "Искусственный Интеллект"
## Наша команда "Дошутились"
**Баранас Павел** - Fullstack-разработчик, 10-й класс, ГБОУ ЛНР "Луганский гуманитарно-экономический лицей-интернат", Луганская Народная Республики <br>
**Салий Александр** - ML-разработчик, 10-й класс, МБОУ "Бобровский образовательный центр «Лидер» имени А. В. Гордеева", Воронежская область <br>
**Суковицына Виктория** - WEB-дизайнер, 9-й класс, МБОУ "СОШ № 13" с. Надежда, Ставропольский край <br>
**Борисова Ксения** - Product-менеджер, 8-й класс, МБОУ "Гимназия № 3 им. Героя Советского Союза Леонида Севрюкова" г. Ставрополь, Ставропольский край
## Использованные технологии
### Для WEB-сайта:
- Python, FastAPI (Backend server)
- Vue.js, Nuxt.js (Frontend server)
- PostgreSQL (База данных)
- Docker (Для компоновки данных)
### Для ИИ / консольной программы:
- Python 3.10+
- FAISS – векторный индекс
- sentence-transformers – эмбеддинги (intfloat/multilingual-e5-large)
- Ollama – локальный запуск LLM (модель qwen2.5:7b)
- PyPDF2, ebooklib, BeautifulSoup4 – парсеры книг
- transformers – extractive QA (опционально)
- numpy, tqdm, chardet – вспомогательные библиотеки
## Реализовано
- **Интерфейсы WEB-сайта (ветка [web](https://github.com/salijaleksandr21-bit/Strelka/tree/web))**
    1. Интерфейс поиска
        - Пользователь вводит свой вопрос
        - Выбирает источник данных (книгу)
        - Получает список цитат
    2. Интерфейс загрузки книг <br>
        Выглядит как список плиток с названием книг
        Каждую книгу можно скачать или удалить
        Также в конце списка есть плитка с добавлением книги
- **Полная консольная программа (ветка [ai](https://github.com/salijaleksandr21-bit/Strelka/tree/ai))** <br>
При проверке решения рекомендуется опираться именно на данное решение<br>
Ответы выдаются 3-м методами с помощью BM25, моделью Ollam'ы и гибридом прошлых 2-х способов. Подробнее в коде `indexing`/`processing`
## Инструкция запуска
### Консольная программа
1. Клонируйте репозиторий
```bash
git clone https://github.com/salijaleksandr21-bit/Strelka.git -b ai
cd Strelka
```
2. Создайте и активируйте виртуальное окружение (рекомендуется)
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```
3. Установите Python-зависимости
```bash
pip install -r requirements.txt
```
4. Установите и запустите Ollama. Скачайте Ollama и запустите сервер в отдельном окне терминала
```bash
ollama serve
```
Загрузите модель для генерации:
```bash
ollama pull qwen2.5:7b
```
5. (Необязательно) Настройте токен Hugging Face
Для ускорения загрузки моделей можно добавить токен:
```bash
export HF_TOKEN="ваш_токен"   # Linux/macOS
set HF_TOKEN=ваш_токен        # Windows
Токен получается на huggingface.co/settings/tokens.
```
6. Запустите файл manage_books.py
```
python manage_books.py
```
7. Запустите файл run_indexing.py
```
python run_indexing.py
```
### WEB
1. Клонируйте репозиторий
```bash
git clone https://github.com/salijaleksandr21-bit/Strelka.git -b web
cd Strelka
```
2. В корне проекта у файла .env.example уберите расширение .example
2. Скачайте и программу Docker Desktop
3. Введите команду для сборки и запуска программы
```cmd
docker-compose build
docker-compose up
```
Сервера будут доступны по адресам:
- Frontend - http://localhost:3000
- Backend - http://localhost:8000/docs
## Демонстрация
### Консольное решение

### WEB-решение
- Интерфейс "Поиск" (компьютер, планшет и телефон)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/search-desktop.png)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/search-tablet.png)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/search-mobile.png)
- Интерфейс "Книги" (компьютер, планшет и телефон)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/books-desktop.png)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/books-tablet.png)
![](https://github.com/salijaleksandr21-bit/Strelka/blob/main/pics/books-mobile.png)
# Благодарим за внимание!