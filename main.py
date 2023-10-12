from typing import Union

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.get("/")
def home(request: Request):
    """
    Returns data to create the homapage Dashboard
    """
    return templates.TemplateResponse(name="home.html", context={
        "request": request,
        "somevar": 2
    })

@app.post("/stock")
def create_stock():
    """
    Creates a stock symbol and saves it to the database
    """
    return {
        "code": "success",
        "message": "stock created"
    }


