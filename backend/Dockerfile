FROM python:3.13-slim

WORKDIR /backend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host ${HOST} --port ${PORT}"]