from dotenv import load_dotenv
load_dotenv()

from api.hitl import start_agent, resume_agent
from fastapi import FastAPI
from api.crud import get_data, cloud_upload
from fastapi.responses import JSONResponse

app = FastAPI()

app.include_router(start_agent.router,prefix="",tags=["HITL AGENT"])
app.include_router(resume_agent.router,prefix="",tags=["HITL AGENT"])

app.include_router(get_data.router,prefix="",tags=["CRUD"])
app.include_router(cloud_upload.router,prefix="",tags=["CRUD"])

@app.get("/")
async def startup():
    return JSONResponse(content="App started Successfully", status_code=200)