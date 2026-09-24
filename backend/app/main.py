from fastapi import FastAPI

from app.services.after_sales import router as after_sales_router
from app.services.chat import router as chat_router

app = FastAPI(title="电商智能客服", version="0.1.0")
app.include_router(chat_router)
app.include_router(after_sales_router)
