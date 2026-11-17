import json
import random
from pathlib import Path
from threading import RLock
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .routes import current_user

router = APIRouter(prefix="/api", tags=["ҰБТ тесттері"])
bank = json.loads(Path(__file__).with_name("questions.json").read_text("utf-8-sig"))
questions = {item["id"]: item for item in bank["questions"]}
attempts = {}
lock = RLock()


class Start(BaseModel):
    topic: int = Field(ge=0, le=10)
    count: Literal[5, 10, 20]


class Answer(BaseModel):
    question: int
    choice: int = Field(ge=0, le=3)


def owned(attempt_id, user):
    attempt = attempts.get(attempt_id)
    if not attempt or attempt["owner"] != user.id:
        raise HTTPException(404, "Тест табылмады.")
    return attempt


def create(user, ids):
    attempt_id = uuid4()
    attempts[attempt_id] = dict(owner=user.id, ids=ids, answers={}, finished=False)
    return {"id": attempt_id}


def view(attempt):
    rows = []
    score = 0
    for i in attempt["ids"]:
        q = questions[i]
        row = {k: q[k] for k in ("id", "text", "options", "level")}
        row["choice"] = attempt["answers"].get(i)
        if attempt["finished"]:
            row["key"] = q["key"]
            score += row["choice"] == q["key"]
        rows.append(row)
    return dict(questions=rows, finished=attempt["finished"],
                score=score if attempt["finished"] else None)


@router.get("/test-topics")
def topics():
    return bank["topics"]


@router.post("/test-attempts", status_code=201)
def start(data: Start, user=Depends(current_user)):
    pool = [i for i in questions if not data.topic or (i - 1)//20 + 1 == data.topic]
    with lock:
        return create(user, random.sample(pool, data.count))


@router.get("/test-attempts")
def history(user=Depends(current_user)):
    with lock:
        return [dict(id=k, count=len(a["ids"]), finished=a["finished"])
                for k, a in reversed(attempts.items()) if a["owner"] == user.id]


@router.get("/test-attempts/{attempt_id}")
def get_attempt(attempt_id: UUID, user=Depends(current_user)):
    with lock:
        return view(owned(attempt_id, user))


@router.patch("/test-attempts/{attempt_id}/answers")
def answer(attempt_id: UUID, data: Answer, user=Depends(current_user)):
    with lock:
        a = owned(attempt_id, user)
        if a["finished"]:
            raise HTTPException(409, "Тест аяқталған.")
        if data.question not in a["ids"]:
            raise HTTPException(422, "Бұл сұрақ тестке кірмейді.")
        a["answers"][data.question] = data.choice
        return view(a)


@router.post("/test-attempts/{attempt_id}/submit")
def submit(attempt_id: UUID, user=Depends(current_user)):
    with lock:
        a = owned(attempt_id, user)
        if len(a["answers"]) != len(a["ids"]):
            raise HTTPException(409, "Барлық сұраққа жауап беріңіз.")
        a["finished"] = True
        return view(a)


@router.post("/test-attempts/{attempt_id}/retry", status_code=201)
def retry(attempt_id: UUID, user=Depends(current_user)):
    with lock:
        a = owned(attempt_id, user)
        missed = [i for i in a["ids"] if a["answers"].get(i) != questions[i]["key"]]
        if not a["finished"] or not missed:
            raise HTTPException(409, "Қайталайтын қате жоқ.")
        return create(user, missed)

