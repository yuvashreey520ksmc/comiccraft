"""
Gemini Pro — detailed comic narration and dialogue from outline
"""

import os
from typing import List, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Prefer Pro; fall back to Flash if Pro is unavailable on the key
MODEL_PRIMARY = "gemini-1.5-pro"
MODEL_FALLBACK = "gemini-1.5-flash"


def generate_story(
    outline: List[Dict[str, Any]],
    character: str = "Hero",
    tone: str = "adventurous",
) -> str:
    """
    Expand the panel outline into full comic-style narration + dialogue.
    Returns a single multi-panel formatted story string.
    """
    outline_text = ""
    for p in outline:
        outline_text += (
            f"\nPanel {p.get('panel_number')}: {p.get('title')}\n"
            f"  Scene: {p.get('scene_description')}\n"
            f"  Caption hint: {p.get('caption')}\n"
        )

    prompt = f"""You are an award-winning comic book scriptwriter.

Expand the following 5-panel outline into a full comic script with narration and dialogue.
Tone: {tone}
Main character: {character}

OUTLINE:
{outline_text}

Write the story panel by panel in this exact format:

=== PANEL 1: <Title> ===
[NARRATION]
<atmospheric narration>

[DIALOGUE]
{character}: "<dialogue>"
(optional other characters)

=== PANEL 2: <Title> ===
...

Keep each panel concise (3–6 lines). Make dialogue natural and matched to the tone.
Return ONLY the formatted script, no extra commentary.
"""

    if not API_KEY:
        return _fallback_story(outline, character)

    for model_name in (MODEL_PRIMARY, MODEL_FALLBACK):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = (response.text or "").strip()
            if text and len(text) > 50:
                return text
        except Exception as e:
            print(f"[gemini_pro] {model_name} error: {e}")
            continue

    return _fallback_story(outline, character)


def generate_story_per_panel(
    outline: List[Dict[str, Any]],
    character: str = "Hero",
    tone: str = "adventurous",
) -> List[Dict[str, str]]:
    """
    Return per-panel narration/dialogue dicts for layout binding.
    Tries to parse the full story; falls back to outline fields.
    """
    full = generate_story(outline, character, tone)
    panels_out = []

    # Simple split by === PANEL
    import re
    parts = re.split(r"===\s*PANEL\s*\d+[:\s]*", full, flags=re.IGNORECASE)
    # parts[0] is preamble; rest are panel bodies
    bodies = [p.strip() for p in parts[1:] if p.strip()]

    for i, panel in enumerate(outline):
        body = bodies[i] if i < len(bodies) else ""
        if not body:
            body = (
                f"[NARRATION]\n{panel.get('scene_description', '')}\n\n"
                f"[DIALOGUE]\n{panel.get('caption', '')}"
            )
        # Extract title from body first line if present
        title = panel.get("title", f"Panel {i + 1}")
        first_line = body.split("\n")[0].strip()
        if first_line and not first_line.startswith("["):
            title = first_line.replace("===", "").strip() or title
            body = "\n".join(body.split("\n")[1:]).strip()

        panels_out.append({
            "panel_number": panel.get("panel_number", i + 1),
            "title": title,
            "narration": body,
            "scene_description": panel.get("scene_description", ""),
            "caption": panel.get("caption", ""),
            "image_prompt": panel.get("image_prompt", ""),
        })
    return panels_out


def _fallback_story(outline: List[Dict], character: str) -> str:
    lines = []
    for p in outline:
        lines.append(f"=== PANEL {p.get('panel_number')}: {p.get('title')} ===")
        lines.append(f"[NARRATION]\n{p.get('scene_description', '')}")
        lines.append(f"[DIALOGUE]\n{p.get('caption', f'{character}: ...')}")
        lines.append("")
    return "\n".join(lines)
