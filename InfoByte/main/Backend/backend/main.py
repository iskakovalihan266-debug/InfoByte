from pathlib import Path
from html import escape
from fastapi.responses import HTMLResponse, FileResponse
from .service import store
from .routes import cookie_name
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .library import router as library_router
from .quiz import router as quiz_router
from .routes import accounts
from .service import Problem

app = FastAPI(title="InfoByte ҰБТ", version="1.0")
app.include_router(accounts)
app.include_router(quiz_router)
app.include_router(library_router)
frontend = Path(__file__).resolve().parents[2] / "Frontend"



@app.exception_handler(Problem)
async def domain_error(request: Request, error: Problem):
    return JSONResponse({"detail": error.message}, status_code=error.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    # Keep submitted passwords out of validation responses.
    fields = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in error.errors()]
    return JSONResponse({"detail": "Енгізілген деректерді тексеріңіз.", "errors": fields}, status_code=422)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(frontend / "index.html")


@app.get("/welcome.html", include_in_schema=False)
def welcome(request: Request):
    try:
        user = store.current(request.cookies.get(cookie_name, ""))
    except Problem:
        return RedirectResponse("/infobyte-auth/login.html", status_code=303)
    page = frontend / "welcome.html"
    if not page.is_file():
        return HTMLResponse("welcome.html файлын main/Frontend ішіне орналастырыңыз.", status_code=503)
    content = page.read_text(encoding="utf-8-sig").replace("{{full_name}}", escape(user.full_name))
    return HTMLResponse(content, headers={"Cache-Control": "no-store"})


app.mount("/infobyte-auth", StaticFiles(directory=frontend / "infobyte-auth"), name="frontend")




app.mount("/shared", StaticFiles(directory=frontend / "shared"), name="shared")

@app.get("/{filename}", include_in_schema=False)
def home_asset(filename: str):
    if filename in {
        "main.css",
        "main.js",
        "logo.jpg",
        "index.html",
        "welcome.css",
        "welcome.js",
        "welcome.html",
        "infobyte-auth/login.html",
        "infobyte-auth/register.html",
        "infobyte-auth/main.css",
        "infobyte-auth/main.js",
        "infobyte-auth/logo.jpg",
        "library.html", "tests.html"}:
        return FileResponse(frontend / filename)
    return JSONResponse({"detail": "Файл табылмады."}, status_code=404)
