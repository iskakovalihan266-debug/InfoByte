import os

from fastapi import APIRouter, Depends, Response
from fastapi.security import APIKeyCookie
from .schemas import Login, Profile, Registration
from .service import store

accounts = APIRouter(prefix="/api", tags=["Accounts"])

cookie_name = "infobyte_session"
cookie = APIKeyCookie(name=cookie_name, auto_error=False)


def current_user(token: str | None = Depends(cookie)) -> Profile:
    return store.current(token or "")


@accounts.post("/users", response_model=Profile, status_code=201)
def register(data: Registration):
    return store.register(data)


@accounts.post("/sessions", response_model=Profile, status_code=201)
def login(data: Login, response: Response):
    user, token, ttl = store.login(data)
    response.set_cookie(cookie_name, token, httponly=True, samesite="strict",
                        secure=os.getenv("COOKIE_SECURE") == "1", path="/",
                        max_age=ttl if data.remember else None)
    return user


@accounts.get("/me", response_model=Profile)
def profile(user: Profile = Depends(current_user)):
    return user


@accounts.delete("/sessions/current", status_code=204)
def logout(token: str | None = Depends(cookie), user: Profile = Depends(current_user)):
    store.logout(token or "")
    response = Response(status_code=204)
    response.delete_cookie(cookie_name, path="/")
    return response




