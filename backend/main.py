from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes import search, book


app = FastAPI(
    title="Backend-сервер обработчик",
    description="Проект разработан в рамках международного соревнования IT-стрелка",
    version="1.2",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


for module in (search, book):
    app.include_router(module.router)
