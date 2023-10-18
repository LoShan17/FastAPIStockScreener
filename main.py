from sqlalchemy.orm import Session
import yfinance
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
import models
from database import engine, SessionLocal
from pydantic import BaseModel
from models import Stock

templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 3 main features of FastApi used here:
# 1) pydantic models and automatic data validation
# 2) dependencies injection in endpoint method signature (db: Session = Depends(get_db))
# 3) background taks (background_tasks.add_task(fetch_stock_data, stock.id))


class StockRequest(BaseModel):
    symbol: str


def get_db():
    """
    yields a database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def fetch_stock_data(id: int):
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.id == id).first()

    yahoo_data = yfinance.Ticker(stock.symbol)
    stock.ma200 = yahoo_data.info["twoHundredDayAverage"]
    stock.ma50 = yahoo_data.info["fiftyDayAverage"]
    stock.price = yahoo_data.info["previousClose"]
    stock.forward_pe = yahoo_data.info["forwardPE"]
    stock.forward_eps = yahoo_data.info["forwardEps"]
    if yahoo_data.info["dividendYield"]:
        stock.dividend_yield = yahoo_data.info["dividendYield"] * 100
    else:
        stock.dividend_yield = 0
    db.add(stock)
    db.commit()


@app.get("/")
def home(request: Request):
    """
    Returns data to create the homapage Dashboard
    """
    return templates.TemplateResponse(name="home.html", context={"request": request})


@app.post("/stock")
def create_stock(
    stock_request: StockRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Creates a stock symbol and saves it to the database
    db: Session = Depends(get_db) is the way FastAPI is managing dependencies injection
    """
    stock = Stock()
    stock.symbol = stock_request.symbol
    db.add(stock)
    db.commit()

    # here the stock sqlalchemy model gets autopoulated during insertion for "id"
    background_tasks.add_task(fetch_stock_data, stock.id)

    return {"code": "success", "message": "stock created"}
