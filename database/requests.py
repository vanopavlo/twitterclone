from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Users


async def get_user_by_api_key(api_key: str, session: AsyncSession):
    stmt = select(Users).where(Users.api_key == api_key )
    result = await session.execute(stmt)

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user
