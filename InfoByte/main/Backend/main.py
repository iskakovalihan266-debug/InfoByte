from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .app.routes import accounts, plans
from .app.schemas import Problem

app = FastAPI(title="InfoByte ҰБТ", version="1.0")
app.include_router(accounts)
app.include_router(plans)


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
    return RedirectResponse("/infobyte-auth/login.html")


app.mount("/infobyte-auth", StaticFiles(directory=Path(__file__).resolve().parents[1] / "Frontend" / "infobyte-auth"), name="frontend")
