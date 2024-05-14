from fastapi import FastAPI
from routers import auth, users

app = FastAPI(docs_url="/")
router = APIRouter()

app.include_router(users.router)
app.include_router(auth.router)
