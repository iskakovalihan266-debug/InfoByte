import os
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from fastapi.security import APIKeyCookie
from .schemas import Login, PlanItem, Profile, Progress, Registration, Topic
from .service import store

accounts = APIRouter(prefix="/api", tags=["Accounts"])
plans = APIRouter(prefix="/api/me/topics", tags=["Study plan"])
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


@plans.post("", response_model=PlanItem, status_code=201)
def add(data: Topic, user: Profile = Depends(current_user)):
    return store.add_topic(user.id, data.title)


@plans.get("", response_model=list[PlanItem])
def topics(done: bool | None = None, user: Profile = Depends(current_user)):
    return store.list_topics(user.id, done)


@plans.patch("/{item_id}", response_model=PlanItem)
def progress(item_id: UUID, data: Progress, user: Profile = Depends(current_user)):
    return store.change_topic(user.id, item_id, data.done)


@plans.delete("/{item_id}", status_code=204)
def remove(item_id: UUID, user: Profile = Depends(current_user)):
    store.delete_topic(user.id, item_id)
    return Response(status_code=204)
