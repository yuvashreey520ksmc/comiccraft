"""
ComicCraft - AI Comic Story Creator
FastAPI entry point
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routes import router

APP_NAME = os.getenv("APP_NAME", "ComicCraft")
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title=APP_NAME,
    description="AI Comic Story Creator using Gemini models + comic panel images",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS, panels, exports)
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
(static_dir / "panels").mkdir(exist_ok=True)
(static_dir / "exports").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "image_mode": os.getenv("IMAGE_MODE", "pillow"),
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "True").lower() == "true"
    # Run as module so "app.main:app" resolves correctly
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
