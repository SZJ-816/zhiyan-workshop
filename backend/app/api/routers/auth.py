"""认证API"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.core.database import get_db
from app.core.config import settings
from app.models.models import User
from app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(user_id: int, account: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "account": account, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.account == req.account).first()
    if not user or not pwd_context.verify(req.password, user.password):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    user.last_login = datetime.now()
    db.commit()
    token = create_token(user.id, user.account)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id, "account": user.account, "realname": user.realname,
            "role": user.role, "avatar_color": user.avatar_color, "email": user.email
        }
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, "account": current_user.account,
        "realname": current_user.realname, "role": current_user.role,
        "avatar_color": current_user.avatar_color, "email": current_user.email,
        "phone": current_user.phone, "department_id": current_user.department_id
    }
