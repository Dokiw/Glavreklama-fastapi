from fastapi import APIRouter,HTTPException

router = APIRouter()
@router.get("/")
async def hub():
    """
    Используется для возврата 200-го статуса на главной странице FastApi()
    :return:
    """
    return HTTPException(200,'Status - True')