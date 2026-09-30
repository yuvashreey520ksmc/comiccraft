"""
ComicCraft FastAPI routes
"""

import os
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from services.gemini_flash import generate_outline
from services.gemini_pro import generate_story_per_panel
from services.image_generator import generate_image
from services.layout_builder import build_comic_layout
from services.exporters import save_pdf

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

APP_NAME = os.getenv("APP_NAME", "ComicCraft")


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Story idea")
    character: str = Field("Hero", description="Main character name")
    setting: str = Field("forest", description="Story setting")
    tone: str = Field("adventurous", description="Story tone")
    art_style: str = Field("comic book", description="Visual art style")


def _run_comic_pipeline(
    prompt: str,
    character: str,
    setting: str,
    tone: str,
    art_style: str,
) -> dict:
    """Full pipeline: outline → story → images → layout → PDF."""
    outline = generate_outline(prompt, character, setting, tone, art_style)
    story_panels = generate_story_per_panel(outline, character, tone)

    image_paths: List[str] = []
    for p in outline:
        img = generate_image(
            image_prompt=p.get("image_prompt", p.get("scene_description", "")),
            panel_number=p.get("panel_number", 1),
            title=p.get("title", ""),
            art_style=art_style,
            character=character,
        )
        image_paths.append(img)

    layout = build_comic_layout(outline, story_panels, image_paths)

    comic_title = f"{character}'s Adventure"
    if prompt:
        comic_title = (prompt[:50] + "…") if len(prompt) > 50 else prompt

    pdf_path = save_pdf(layout, title=comic_title, character=character)

    return {
        "layout": layout,
        "pdf_path": pdf_path,
        "character": character,
        "prompt": prompt,
        "tone": tone,
        "art_style": art_style,
        "setting": setting,
        "title": comic_title,
    }


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
    })


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character: str = Form("Hero"),
    setting: str = Form("forest"),
    tone: str = Form("adventurous"),
    art_style: str = Form("comic book"),
):
    try:
        result = _run_comic_pipeline(prompt, character, setting, tone, art_style)
        return templates.TemplateResponse("comic_preview.html", {
            "request": request,
            "app_name": APP_NAME,
            "layout": result["layout"],
            "pdf_path": result["pdf_path"],
            "character": result["character"],
            "prompt": result["prompt"],
            "tone": result["tone"],
            "art_style": result["art_style"],
            "title": result["title"],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comic generation failed: {e}")


@router.post("/generate-comic/json")
async def generate_comic_json(body: PromptRequest):
    try:
        result = _run_comic_pipeline(
            body.prompt, body.character, body.setting, body.tone, body.art_style
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf: Optional[str] = None):
    return templates.TemplateResponse("export_success.html", {
        "request": request,
        "app_name": APP_NAME,
        "pdf_path": pdf or "",
    })


@router.get("/test-image")
async def test_image(prompt: str = "a brave fox in an enchanted forest, comic book style"):
    path = generate_image(prompt, panel_number=0, title="Test")
    return {"image_path": path, "prompt": prompt}


@router.get("/download")
async def download_pdf(path: str):
    """Serve a generated PDF for download."""
    # path is like /static/exports/comic_xxx.pdf
    if not path.startswith("/static/exports/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    file_path = BASE_DIR / path.lstrip("/")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name,
    )
