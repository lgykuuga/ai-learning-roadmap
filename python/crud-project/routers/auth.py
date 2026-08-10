import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AdminSession, AdminUser
from schemas import ApiResult, LoginRequest

router = APIRouter(prefix="/api/admin", tags=["后台登录"])


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


async def get_current_admin(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(AdminSession, AdminUser)
        .join(AdminUser, AdminSession.user_id == AdminUser.id)
        .where(AdminSession.token == token, AdminSession.expires_at > now)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="登录已过期")
    return row[1]


@router.post("/login", response_model=ApiResult)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == body.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(AdminSession(
        user_id=user.id,
        token=token,
        expires_at=now + timedelta(days=1),
    ))
    await db.commit()
    return ApiResult(data={"token": token, "username": user.username})


@router.get("/me", response_model=ApiResult)
async def me(user: AdminUser = Depends(get_current_admin)):
    return ApiResult(data={"username": user.username})


@router.post("/logout", response_model=ApiResult)
async def logout(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if authorization and authorization.startswith("Bearer "):
        result = await db.execute(
            select(AdminSession).where(AdminSession.token == authorization[7:])
        )
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()
    return ApiResult(msg="已退出")
