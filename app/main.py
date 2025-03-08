"""Deepclaude"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.manager import ConfigManager
from .api import chat, models, config
from .utils.errors import ConfigError, ConfigLoadError, ConfigSaveError
from .utils.logger import LOGGER


# Lifespan
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan with enhanced error handling"""
    try:
        # Initialize the config manager
        ConfigManager.initialize()
        yield
    except ConfigLoadError as e:
        LOGGER.critical(
            "Configuration loading failed: %s\n\nPlease check your config files.",
            e.reason_msg,
        )
        sys.exit(1)
    except ConfigSaveError as e:
        LOGGER.critical(
            "Configuration saving failed: %s\n\nPlease check your permissions and disk space.",
            e.reason_msg,
        )
        sys.exit(1)
    except ConfigError as e:
        LOGGER.critical(
            "Configuration error: %s\n\nPlease check your configuration.",
            e.reason_msg,
        )
        sys.exit(1)
    except Exception as e:
        LOGGER.critical("Unexpected error during initialization: %s", str(e))
        sys.exit(1)
    finally:
        # Release the config manager
        if ConfigManager.instance():
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


# Enhanced global exception handling
@app.exception_handler(ConfigLoadError)
async def config_load_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration loading error",
            "detail": str(exc),
            "solution": "Please check your configuration files"
        },
    )

@app.exception_handler(ConfigSaveError)
async def config_save_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration saving error",
            "detail": str(exc),
            "solution": "Please check your permissions and disk space"
        },
    )

@app.exception_handler(ConfigError)
async def config_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration error",
            "detail": str(exc),
            "solution": "Please check your configuration"
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    LOGGER.error("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "solution": "Please contact support"
        },
    )

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    LOGGER.error("Runtime error: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Runtime error",
            "detail": str(exc),
            "solution": "Please check your request and try again"
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=ConfigManager.instance().system.host,
        port=ConfigManager.instance().system.port,
        reload=True,
    )
