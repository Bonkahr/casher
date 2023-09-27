from fastapi import FastAPI

from database import models
from database.database import engine
from routers import user_route, expenditure
from auth import authentication


app = FastAPI()

models.Base.metadata.create_all(engine)

app.include_router(authentication.router)
app.include_router(user_route.router)
app.include_router(expenditure.router)
