"""
Export comic layout to a multi-page PDF using fpdf2.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

EXPORTS_DIR = Path(__file__).resolve().parent.parent / "static" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Project root for resolving /static/... paths
ROOT = Path(__file__).resolve().parent.parent


class ComicPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 120)
        self.cell(0, 8, "ComicCraft - AI Comic Story Creator", align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _resolve_image(path: str) -> str:
    """Convert /static/panels/xxx.png to absolute filesystem path."""
    if not path:
        return ""
    if path.startswith("/static/"):
        return str(ROOT / path.lstrip("/"))
    if path.startswith("static/"):
        return str(ROOT / path)
    return path


def save_pdf(
    layout: List[Dict[str, Any]],
    title: str = "My Comic",
    character: str = "Hero",
) -> str:
    """
    Create a PDF with one page per panel (image + text).
    Returns web path like /static/exports/comic_YYYYMMDD_HHMMSS.pdf
    """
    pdf = ComicPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)

    # Cover page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(40, 40, 80)
    pdf.ln(50)
    pdf.multi_cell(0, 14, title[:80], align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 100)
    pdf.cell(0, 10, f"Starring: {character}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, f"Created with ComicCraft · {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

    for panel in layout:
        pdf.add_page()

        # Panel title
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(30, 30, 60)
        panel_title = f"Panel {panel.get('panel_number', '')}: {panel.get('title', '')}"
        pdf.multi_cell(0, 9, panel_title)
        pdf.ln(3)

        # Image
        img_path = _resolve_image(panel.get("image", ""))
        if img_path and os.path.isfile(img_path):
            try:
                # Fit image to page width with margin
                max_w = 180
                pdf.image(img_path, x=15, w=max_w)
                pdf.ln(6)
            except Exception as e:
                pdf.set_font("Helvetica", "I", 10)
                pdf.cell(0, 8, f"[Image could not be embedded: {e}]")
                pdf.ln(6)
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 80, 80)
            pdf.cell(0, 8, "[No image for this panel]")
            pdf.ln(6)

        # Scene description
        scene = panel.get("scene_description") or ""
        if scene:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(90, 90, 110)
            pdf.multi_cell(0, 5, scene)
            pdf.ln(3)

        # Narration / dialogue
        narration = panel.get("narration") or panel.get("caption") or ""
        if narration:
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20, 20, 30)
            # Clean markdown-ish markers for PDF
            clean = narration.replace("[NARRATION]", "Narration:").replace("[DIALOGUE]", "Dialogue:")
            pdf.multi_cell(0, 6, clean)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:30]
    filename = f"comic_{safe_title}_{timestamp}.pdf"
    out_path = EXPORTS_DIR / filename
    pdf.output(str(out_path))
    return f"/static/exports/{filename}"
