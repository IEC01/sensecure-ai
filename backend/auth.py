#!/usr/bin/env python3
"""
SenSecure AI — Authentification JWT (sans bcrypt)
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import hashlib, os

SECRET_KEY = os.getenv("SECRET_KEY", "sensecure-ai-unchk-2026")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

USERS_DB = {
    "admin": {
        "username":        "admin",
        "full_name":       "Administrateur SenSecure",
        "email":           "admin@sensecure.sn",
        "hashed_password": hash_password("sensecure2026"),
        "role":            "admin",
        "disabled":        False,
    },
    "analyste": {
        "username":        "analyste",
        "full_name":       "Analyste Sécurité",
        "email":           "analyste@sensecure.sn",
        "hashed_password": hash_password("analyste2026"),
        "role":            "analyste",
        "disabled":        False,
    },
}

class Token(BaseModel):
    access_token: str
    token_type:   str
    username:     str
    role:         str

def get_user(username: str):
    return USERS_DB.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Utilisateur désactivé")
    return current_user
