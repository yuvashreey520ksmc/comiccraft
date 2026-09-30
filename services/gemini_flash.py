"""
Gemini Flash — structured 5-panel comic outline generation
"""

import os
import json
import re
from typing import List, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash"


def _parse_json(text: str) -> Any:
    text = text.strip()
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return None


def generate_outline(
    prompt: str,
    character: str = "Hero",
    setting: str = "forest",
    tone: str = "adventurous",
    art_style: str = "comic book",
) -> List[Dict[str, Any]]:
    """
    Generate a structured 5-panel comic outline.
    Each panel: panel_number, title, scene_description, image_prompt, caption
    """
    system_prompt = f"""You are a professional comic book writer and storyboard artist.

Create a complete 5-panel comic outline based on the user's idea.

User inputs:
- Story idea: {prompt}
- Main character: {character}
- Setting: {setting}
- Tone: {tone}
- Art style: {art_style}

Rules:
1. Exactly 5 panels that form a complete mini-story (setup → rising action → climax → resolution).
2. Each panel needs a short title, a vivid scene description, a detailed image prompt suitable for an illustrator, and a brief caption.
3. Image prompts must describe visual composition, character pose, environment, lighting, and style "{art_style}".
4. Keep language engaging and matched to the tone "{tone}".
5. Character name must appear as "{character}".

Respond ONLY with valid JSON array (no markdown outside the array):
[
  {{
    "panel_number": 1,
    "title": "Panel title",
    "scene_description": "What happens in this panel",
    "image_prompt": "Detailed visual description for illustration, {art_style} style, ...",
    "caption": "Short caption or dialogue line"
  }},
  ...
]
"""

    if not API_KEY:
        return _fallback_outline(prompt, character, setting, tone, art_style)

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(system_prompt)
        data = _parse_json(response.text)
        if isinstance(data, list) and len(data) >= 3:
            # Normalize
            panels = []
            for i, p in enumerate(data[:5]):
                panels.append({
                    "panel_number": p.get("panel_number", i + 1),
                    "title": p.get("title", f"Panel {i + 1}"),
                    "scene_description": p.get("scene_description", ""),
                    "image_prompt": p.get("image_prompt", p.get("scene_description", "")),
                    "caption": p.get("caption", ""),
                })
            while len(panels) < 5:
                n = len(panels) + 1
                panels.append({
                    "panel_number": n,
                    "title": f"Panel {n}",
                    "scene_description": f"Continuation of the story for {character}.",
                    "image_prompt": f"{art_style} style, {character} in {setting}, comic panel",
                    "caption": "...",
                })
            return panels
        return _fallback_outline(prompt, character, setting, tone, art_style)
    except Exception as e:
        print(f"[gemini_flash] Error: {e}")
        return _fallback_outline(prompt, character, setting, tone, art_style)


def _fallback_outline(prompt, character, setting, tone, art_style) -> List[Dict]:
    """Demo outline when API key is missing or fails."""
    return [
        {
            "panel_number": 1,
            "title": "The Beginning",
            "scene_description": f"{character} stands at the edge of the {setting}, ready for adventure. The story begins: {prompt[:80]}",
            "image_prompt": f"{art_style} style comic panel, {character} looking determined at the entrance of a {setting}, dramatic lighting, vibrant colors",
            "caption": f"{character}: \"This is where it all begins...\"",
        },
        {
            "panel_number": 2,
            "title": "The Discovery",
            "scene_description": f"Deep in the {setting}, {character} discovers something unexpected that changes everything.",
            "image_prompt": f"{art_style} style, {character} discovering a glowing object in the {setting}, surprised expression, detailed background",
            "caption": f"{character}: \"What is this?!\"",
        },
        {
            "panel_number": 3,
            "title": "The Challenge",
            "scene_description": f"A sudden obstacle appears. The tone turns {tone} as {character} must act quickly.",
            "image_prompt": f"{art_style} style action panel, {character} facing a challenge in the {setting}, dynamic pose, intense atmosphere",
            "caption": "The path ahead is blocked!",
        },
        {
            "panel_number": 4,
            "title": "The Turning Point",
            "scene_description": f"Using courage and wit, {character} finds a way forward. The climax of the story.",
            "image_prompt": f"{art_style} style, heroic moment of {character} overcoming the obstacle, triumphant pose, cinematic composition",
            "caption": f"{character}: \"I won't give up!\"",
        },
        {
            "panel_number": 5,
            "title": "The Resolution",
            "scene_description": f"Peace returns to the {setting}. {character} reflects on the journey with a sense of growth.",
            "image_prompt": f"{art_style} style peaceful ending scene, {character} smiling in the {setting} at sunset, warm colors, satisfying conclusion",
            "caption": f"{character}: \"What an adventure... until next time.\"",
        },
    ]
