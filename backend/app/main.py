"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.schema import init_schema
from app.db.session import get_conn
from app.routers import chat, geo, profile, query, summary, upload


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DataLens API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize the catalog tables eagerly. Doing this in create_app() rather
    # than an @app.on_event startup handler ensures the schema exists for both
    # real serving and TestClient regardless of lifespan handling.
    with get_conn() as conn:
        init_schema(conn)

    app.include_router(upload.router)
    app.include_router(profile.router)
    app.include_router(geo.router)
    app.include_router(query.router)
    app.include_router(chat.router)
    app.include_router(summary.router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
