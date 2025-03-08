"""Deepclaude"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config.manager import ConfigManager
from .api import chat, models, config


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the config manager
    ConfigManager.initialize()
    yield
    # Release the config manager
    await ConfigManager.instance().close()


# Create FastAPI app
app = FastAPI(
    title="DeepClaude",
    lifespan=lifespan,
    dependencies=[Depends(ConfigManager.instance().validate_api_key)],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ConfigManager.instance().system.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(models.router, prefix="/v1/models", tags=["Models"])
app.include_router(config.router, prefix="/v1/config", tags=["Config"])


# 全局异常处理（示例）
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=ConfigManager.instance().system.host,
        port=ConfigManager.instance().system.port,
        reload=True,
    )
