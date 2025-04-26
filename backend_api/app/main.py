from fastapi import FastAPI
from backend_api.app.routers import gfpgan

app = FastAPI()

app.include_router(gfpgan.router) 