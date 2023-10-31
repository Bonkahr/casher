from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .database import models
from database.database import engine
from routers import user_route, expenditure
from auth import authentication


app = FastAPI()

origins = ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(engine)

app.include_router(authentication.router)
app.include_router(user_route.router)
app.include_router(expenditure.router)
app.mount("/images", StaticFiles(directory="images"), name="images")


if __name__ == "main":
    uvicorn.run(app, host="0.0.0.0", port=8000)
