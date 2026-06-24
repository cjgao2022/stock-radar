from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from data.cache import init_db
from data.scheduler import start_scheduler
from api.routes_overview import router as overview_router
from api.routes_boards import router as boards_router
from api.routes_stocks import router as stocks_router
from api.routes_valuation import router as valuation_router
from api.routes_macro import router as macro_router
from api.routes_news import router as news_router
from api.routes_leaders import router as leaders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="Stock Radar", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(overview_router)
app.include_router(boards_router)
app.include_router(stocks_router)
app.include_router(valuation_router)
app.include_router(macro_router)
app.include_router(news_router)
app.include_router(leaders_router)


@app.get("/")
def page_overview(request: Request):
    return templates.TemplateResponse(request=request, name="overview.html")


@app.get("/boards")
def page_boards(request: Request):
    return templates.TemplateResponse(request=request, name="boards.html")


@app.get("/boards/{board_type}/{board_name}")
def page_board_detail(request: Request, board_type: str, board_name: str):
    label = "概念板块" if board_type == "concept" else "行业板块"
    return templates.TemplateResponse(
        request=request,
        name="board_detail.html",
        context={"board_type": board_type, "board_name": board_name, "board_type_label": label},
    )


@app.get("/stocks")
def page_stocks(request: Request):
    return templates.TemplateResponse(request=request, name="stocks.html")


@app.get("/etf")
def page_etf(request: Request):
    return templates.TemplateResponse(request=request, name="etf.html")


@app.get("/valuation")
def page_valuation(request: Request):
    return templates.TemplateResponse(request=request, name="valuation.html")


@app.get("/macro")
def page_macro(request: Request):
    return templates.TemplateResponse(request=request, name="macro.html")


@app.get("/news")
def page_news(request: Request):
    return templates.TemplateResponse(request=request, name="news.html")


@app.get("/leaders")
def page_leaders(request: Request):
    return templates.TemplateResponse(request=request, name="leaders.html")

