"""
Comic panel image generation.

Default mode: Pillow-based stylized comic panels (fast, no GPU, always works).
Optional mode: local Stable Diffusion via Diffusers (IMAGE_MODE=diffusers).
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

IMAGE_MODE = os.getenv("IMAGE_MODE", "pillow").lower()
PANELS_DIR = Path(__file__).resolve().parent.parent / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)

# Color palettes by art style
STYLE_COLORS = {
    "anime": {"bg": (255, 240, 245), "accent": (255, 105, 180), "text": (40, 20, 60), "border": (200, 80, 140)},
    "comic book": {"bg": (255, 250, 230), "accent": (220, 50, 50), "text": (20, 20, 20), "border": (30, 30, 30)},
    "pixel art": {"bg": (40, 50, 70), "accent": (100, 220, 100), "text": (230, 255, 230), "border": (80, 200, 80)},
    "realistic": {"bg": (245, 245, 240), "accent": (70, 100, 130), "text": (30, 30, 30), "border": (60, 80, 100)},
    "cartoon": {"bg": (255, 255, 220), "accent": (255, 160, 50), "text": (50, 30, 10), "border": (255, 140, 0)},
}


def _safe_filename(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "_", text).strip("_")
    return text[:max_len] or "panel"


def _get_font(size: int):
    # Try common system fonts; fall back to default
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/comic.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw) -> list:
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def generate_image_pillow(
    image_prompt: str,
    panel_number: int = 1,
    title: str = "",
    art_style: str = "comic book",
    character: str = "Hero",
) -> str:
    """Create a stylized comic panel image with Pillow."""
    style_key = art_style.lower().strip()
    colors = STYLE_COLORS.get(style_key, STYLE_COLORS["comic book"])

    W, H = 768, 512
    img = Image.new("RGB", (W, H), colors["bg"])
    draw = ImageDraw.Draw(img)

    # Outer border (comic frame)
    border = 8
    draw.rectangle([0, 0, W - 1, H - 1], outline=colors["border"], width=border)
    draw.rectangle([border + 2, border + 2, W - border - 3, H - border - 3], outline=colors["accent"], width=3)

    # Header bar
    header_h = 48
    draw.rectangle([border, border, W - border, border + header_h], fill=colors["accent"])
    font_title = _get_font(22)
    header_text = f"PANEL {panel_number}" + (f"  ·  {title}" if title else "")
    draw.text((border + 16, border + 12), header_text[:60], fill=(255, 255, 255), font=font_title)

    # Decorative "art" area — abstract shapes suggesting a scene
    import random
    rng = random.Random(hashlib.md5(image_prompt.encode()).hexdigest())
    art_top = border + header_h + 10
    art_bottom = H - 100
    for _ in range(12):
        x1 = rng.randint(border + 20, W // 2)
        y1 = rng.randint(art_top, art_bottom - 40)
        x2 = x1 + rng.randint(40, 180)
        y2 = y1 + rng.randint(30, 120)
        alpha_color = tuple(min(255, c + rng.randint(-40, 40)) for c in colors["accent"])
        # Soft fill
        fill = tuple(int(colors["bg"][i] * 0.7 + alpha_color[i] * 0.3) for i in range(3))
        draw.ellipse([x1, y1, x2, y2], fill=fill, outline=colors["border"])

    # Character label bubble
    font_char = _get_font(18)
    bubble = f"★ {character}"
    bb = draw.textbbox((0, 0), bubble, font=font_char)
    bw, bh = bb[2] - bb[0] + 24, bb[3] - bb[1] + 16
    bx, by = W - border - bw - 20, art_top + 10
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=12, fill=(255, 255, 255), outline=colors["border"], width=2)
    draw.text((bx + 12, by + 6), bubble, fill=colors["text"], font=font_char)

    # Prompt / scene text at bottom
    font_body = _get_font(14)
    prompt_short = image_prompt[:200] + ("…" if len(image_prompt) > 200 else "")
    lines = _wrap_text(prompt_short, font_body, W - 2 * border - 30, draw)
    y = H - 90
    draw.rectangle([border + 5, y - 8, W - border - 5, H - border - 5], fill=(255, 255, 255), outline=colors["border"])
    for line in lines[:4]:
        draw.text((border + 16, y), line, fill=colors["text"], font=font_body)
        y += 18

    # Save
    fname = f"panel_{panel_number}_{_safe_filename(title or image_prompt)}.png"
    path = PANELS_DIR / fname
    img.save(path, "PNG")
    return f"/static/panels/{fname}"


def generate_image_diffusers(image_prompt: str, panel_number: int = 1, title: str = "") -> Optional[str]:
    """Local Stable Diffusion via Diffusers (optional, heavy)."""
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError:
        print("[image_generator] torch/diffusers not installed — using Pillow fallback")
        return None

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None,
        )
        pipe = pipe.to(device)
        if device == "cpu":
            pipe.enable_attention_slicing()

        prompt = f"comic book panel illustration, {image_prompt}, vibrant colors, clear line art"
        result = pipe(prompt, num_inference_steps=20 if device == "cuda" else 12, guidance=(768, 512)).images[0]

        fname = f"panel_{panel_number}_{_safe_filename(title or image_prompt)}.png"
        path = PANELS_DIR / fname
        result.save(path)
        return f"/static/panels/{fname}"
    except Exception as e:
        print(f"[image_generator] Diffusers failed: {e}")
        return None


def generate_image(
    image_prompt: str,
    panel_number: int = 1,
    title: str = "",
    art_style: str = "comic book",
    character: str = "Hero",
) -> str:
    """
    Generate a comic panel image.
    Uses Diffusers only when IMAGE_MODE=diffusers and libraries are available;
    otherwise always uses fast Pillow comic-style panels.
    """
    if IMAGE_MODE == "diffusers":
        path = generate_image_diffusers(image_prompt, panel_number, title)
        if path:
            return path
    return generate_image_pillow(image_prompt, panel_number, title, art_style, character)
