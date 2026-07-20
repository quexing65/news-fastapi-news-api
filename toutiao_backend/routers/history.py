from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from models.users import User
from schemas.history import HistoryAddRequest
from utils.auth import get_current_user
from utils.response import success_response


router = APIRouter(prefix="/api/history", tags = ["history"])


@router.post("/add")
async def add_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    return success_response(message="添加浏览记录成功")