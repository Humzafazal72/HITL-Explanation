from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.hitl import start_agent, resume_agent
from api.crud import get_data, cloud_upload, delete_figures

app = FastAPI()

app.include_router(start_agent.router,prefix="",tags=["HITL AGENT"])
app.include_router(resume_agent.router,prefix="",tags=["HITL AGENT"])

app.include_router(get_data.router,prefix="",tags=["CRUD"])
app.include_router(cloud_upload.router,prefix="",tags=["CRUD"])
app.include_router(delete_figures.router,prefix="",tags=["CRUD"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # any origin
    allow_credentials=True,
    allow_methods=["*"],          # any HTTP method
    allow_headers=["*"],          # any headers
)

@app.get("/health")
async def health():
    return JSONResponse(content="App started Successfully", status_code=200)