from fastapi import APIRouter,HTTPException

route = APIRouter()

@route.get("/")
async def hub():
    return HTTPException(200,'Status - True')