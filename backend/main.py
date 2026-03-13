from fastapi import FastAPI
from routes import MODULES


app = FastAPI(
    title="Backend-сервер обработчик",
    description="Проект разработан в рамках международного соревнования IT-стрелка",
    version="1.2",
    debug=True,
)


for module in MODULES:
    app.include_router(module.router)
