from __future__ import annotations

import contextlib
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from cashflow.connectors.registry import load_registry
from cashflow.service.api import router
from cashflow.utils.config import get_settings

UI_DIR = Path(__file__).resolve().parent / "resources" / "ui"
UI_INDEX_PATH = UI_DIR / "index.html"
UI_ASSETS_DIR = UI_DIR / "assets"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.connectors = load_registry(get_settings().connectors_dir)
    yield


def _add_cache_headers(request: Request, response: Response) -> None:
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")


def _ui_index() -> Response:
    if not UI_INDEX_PATH.is_file():
        return HTMLResponse(
            "<h1>UI assets missing</h1><p>The Cashflow API is available under /api.</p>",
            status_code=503,
        )
    return FileResponse(UI_INDEX_PATH)


def create_rest_app() -> FastAPI:
    app = FastAPI(title="Cashflow API", version=version("cashflow"))
    app.include_router(router, prefix="/api")
    return app


def create_application() -> FastAPI:
    app = create_rest_app()
    app.router.lifespan_context = lifespan

    @app.middleware("http")
    async def cache_headers(request: Request, call_next):
        response = await call_next(request)
        _add_cache_headers(request, response)
        return response

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse("/app/")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    async def ui() -> Response:
        return _ui_index()

    if UI_ASSETS_DIR.is_dir():
        app.mount("/app/assets", StaticFiles(directory=UI_ASSETS_DIR), name="ui-assets")

    return app


app = create_application()
