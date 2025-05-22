from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.db import users_collection
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from models.auth import User, Token, Login
from fastapi.security.utils import get_authorization_scheme_param

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password):
    return pwd_context.hash(plain_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = (
            datetime.now().timestamp()
            + timedelta(minutes=expires_delta).total_seconds()
        )
    else:
        expire = datetime.now().timestamp() + timedelta(minutes=30).total_seconds()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "$Trong##ecret", algorithm="HS256")
    return encoded_jwt


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str:

        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer":
            return param

        auth_cookie = request.cookies.get("Authorization")
        if auth_cookie:
            print("Auth cookie:", auth_cookie)
            auth_cookie = auth_cookie.strip('"')
            scheme, param = get_authorization_scheme_param(auth_cookie)
            print("Scheme:", scheme)
            print("Param:", param)
            if scheme.lower() == "bearer":
                return param

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/login")

from typing import Optional


class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=400, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, key="$Trong##ecret", algorithms=["HS256"])
        email: str = payload.get("sub")
        username = payload.get("username")
        print(f"email: {email}, username: {username}")
        if username is None:
            raise credentials_exception
        token_data = TokenData(email=email, username=username)
        return token_data
    except JWTError:
        raise credentials_exception


auth_router = APIRouter()


@auth_router.post("/api/login", response_model=Token)
async def login(user: Login):
    existing_user = users_collection.find_one({"email": user.email})
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(
        data={"sub": existing_user["email"], "username": existing_user["username"]}
    )
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"access_token": token, "token_type": "bearer"},
    )
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {token}",
    )
    return response


@auth_router.post("/api/register")
async def register(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = hash_password(user.password)
    users_collection.insert_one(
        {"username": user.username, "email": user.email, "password": hashed_password}
    )
    return {"message": "User registered successfully"}
