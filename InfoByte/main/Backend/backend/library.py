from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .pdf_search import clean, search_collection
from .routes import current_user


class Passage(BaseModel):
    book: str
    page: int
    before: str
    match: str
    after: str


class SearchResult(BaseModel):
    results: list[Passage]
    notice: str


BOOKS = Path(__file__).resolve().parents[2] / "Frontend" / "books"
router = APIRouter(prefix="/api/books", dependencies=[Depends(current_user)])

@router.get("/search", response_model=SearchResult)
def search_books(q: str = Query(min_length=1, max_length=120)):
    if not clean(q):
        raise HTTPException(422, "Термин енгізіңіз.")
    return search_collection(BOOKS, q)