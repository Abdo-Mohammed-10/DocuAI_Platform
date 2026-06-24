from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from services.api_gateway.middleware.request_id import RequestIDMiddleware
from services.api_gateway.middleware.tracing import TracingMiddleware
from services.api_gateway.routers import analytics, auth, chat, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway starting...")
    yield
    print("API Gateway shutting down...")


app = FastAPI(
    title="Smart Doc Intelligence — API Gateway",
    version="0.1.0",
    description="Unified API for Document Intelligence Platform",
    lifespan=lifespan,
)
Instrumentator().instrument(app).expose(app)

# Middleware 
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers 
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.get("/")
async def root():
    return {
        "message": "Smart Document Intelligence Platform",
        "docs":    "/docs",
        "version": "0.1.0",
    }