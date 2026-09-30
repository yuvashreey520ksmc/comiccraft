"""
Organize generated images + story text into a structured comic layout.
"""

from typing import List, Dict, Any


def build_comic_layout(
    outline: List[Dict[str, Any]],
    story_panels: List[Dict[str, Any]],
    image_paths: List[str],
) -> List[Dict[str, Any]]:
    """
    Merge outline, per-panel story text, and image paths into a single layout list.

    Each item:
      panel_number, title, image, scene_description, narration, caption, image_prompt
    """
    layout = []
    n = max(len(outline), len(story_panels), len(image_paths))

    for i in range(n):
        o = outline[i] if i < len(outline) else {}
        s = story_panels[i] if i < len(story_panels) else {}
        img = image_paths[i] if i < len(image_paths) else ""

        layout.append({
            "panel_number": o.get("panel_number") or s.get("panel_number") or (i + 1),
            "title": s.get("title") or o.get("title") or f"Panel {i + 1}",
            "image": img,
            "scene_description": o.get("scene_description") or s.get("scene_description") or "",
            "narration": s.get("narration") or o.get("caption") or "",
            "caption": o.get("caption") or s.get("caption") or "",
            "image_prompt": o.get("image_prompt") or s.get("image_prompt") or "",
        })

    return layout
