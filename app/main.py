from fastapi import FastAPI
from api import routes_hitl
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5500",  # if using Live Server in VSCode
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # very important (includes OPTIONS)
    allow_headers=["*"],
)

app.include_router(routes_hitl.router,prefix="",tags=["HITL"])