from typing import Union

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import models
from database import engine, SessionLocal

templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home(request: Request):
    """
    Returns data to create the homapage Dashboard
    """
    return templates.TemplateResponse(name="home.html", context={"request": request})


@app.post("/stock")
def create_stock():
    """
    Creates a stock symbol and saves it to the database
    """
    return {"code": "success", "message": "stock created"}
