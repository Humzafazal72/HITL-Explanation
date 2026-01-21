from fastapi import FastAPI
from api import routes_hitl
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(routes_hitl.router,prefix="",tags=["HITL"])

@app.get("/")
async def startup():
    return JSONResponse(content="App started Successfully", status_code=200)