"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.pipeline import get_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the pipeline (loads models) before serving requests
    logger.info("Warming up RAG pipeline…")
    get_pipeline()
    logger.info("Startup complete — ready to serve.")
    yield
    logger.info("Shutdown.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG System API",
        description=(
            "A production-ready Retrieval-Augmented Generation system with "
            "5 layers: Query Processing → Vector Retrieval → Re-ranking → "
            "Generation → Evaluation"
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
