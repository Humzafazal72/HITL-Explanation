from fastapi import FastAPI
from api import routes_hitl, routes_crud
from fastapi.responses import JSONResponse

app = FastAPI()

app.include_router(routes_hitl.router,prefix="",tags=["HITL"])
app.include_router(routes_crud.router,prefix="",tags=["CRUD"])

@app.get("/")
async def startup():
    return JSONResponse(content="App started Successfully", status_code=200)