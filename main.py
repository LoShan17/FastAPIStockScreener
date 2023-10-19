from sqlalchemy.orm import Session
import yfinance
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
import models
from database import engine, SessionLocal
from pydantic import BaseModel
from models import Stock
import logging

logging.basicConfig(level=logging.INFO)

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
def home(
    request: Request,
    forward_pe=None,
    dividend_yield=None,
    ma50=None,
    ma200=None,
    db: Session = Depends(get_db),
):
    """
    Returns data to create the homapage Dashboard
    """
    # this is not necessary because db: Session = Depends(get_db)
    # db = SessionLocal()

    stocks = db.query(Stock)
    if forward_pe:
        stocks = stocks.filter(Stock.forward_pe < forward_pe)

    if dividend_yield:
        stocks = stocks.filter(Stock.dividend_yield > dividend_yield)

    if ma50:
        stocks = stocks.filter(Stock.price > Stock.ma50)

    if ma200:
        stocks = stocks.filter(Stock.price > Stock.ma200)

    logging.info(msg=f"db returned stocks: {stocks}")
    return templates.TemplateResponse(
        name="home.html",
        context={
            "request": request,
            "stocks": stocks,
            "dividend_yield": dividend_yield,
            "forward_pe": forward_pe,
            "ma200": ma200,
            "ma50": ma50,
        },
    )


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
    logging.info(msg=f"Adding to the database stock symbol: {stock.symbol}")
    db.add(stock)
    db.commit()

    # here the stock sqlalchemy model gets autopoulated during insertion for "id"
    logging.info(msg=f"Sending background task to fetch stock symbol: {stock.symbol}")
    background_tasks.add_task(fetch_stock_data, stock.id)

    return {"code": "success", "message": "stock created"}
