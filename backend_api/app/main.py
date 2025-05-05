from fastapi import FastAPI
from backend_api.app.routers import gfpgan, fallai_webhook

app = FastAPI()

app.include_router(gfpgan.router)
app.include_router(fallai_webhook.router)
