from fastapi import APIRouter,HTTPException

router = APIRouter()

@router.get("/")
async def hub():
    return HTTPException(200,'Status - True')