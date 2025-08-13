from fastapi import FastAPI
import importlib
import pkgutil


app = FastAPI()



async def on_startup():
    # Импортируем все модели при запуске
    pass


@app.get("/")
async def root()    :
    return {"message": "Hello World"}
    