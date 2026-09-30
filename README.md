# ComicCraft — AI Comic Story Creator

Generate **5-panel comics** from a simple story prompt using **Google Gemini** (outline + narration/dialogue) and comic-style panel illustrations. Export the full comic as a **PDF**.

---

## Features

- Story outline via **Gemini 1.5 Flash**
- Narration & dialogue via **Gemini 1.5 Pro** (falls back to Flash)
- Panel illustrations (fast **Pillow** comic frames by default; optional local **Stable Diffusion**)
- On-screen comic preview
- Multi-page **PDF export** (FPDF2)
- JSON API for programmatic use

---

## Project structure

```
ComicCraft/
├── main.py                 # Run: python main.py
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py             # FastAPI app
│   └── routes.py           # All routes
├── services/
│   ├── gemini_flash.py     # Panel outline
│   ├── gemini_pro.py       # Story / dialogue
│   ├── image_generator.py  # Panel images
│   ├── layout_builder.py
│   └── exporters.py        # PDF export
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
└── static/
    ├── css/style.css
    ├── panels/             # Generated panel images
    └── exports/            # Generated PDFs
```

---

## Quick start (Windows)

```cmd
cd ComicCraft

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
```

Edit `.env` and set:

```
GEMINI_API_KEY=your_key_from_https://aistudio.google.com/app/apikey
```

(If the key is empty, the app still runs with **demo story text** and illustrated panels.)

```cmd
python main.py
```

Open: **http://127.0.0.1:8000**

API docs: **http://127.0.0.1:8000/docs**

---

## macOS / Linux

```bash
cd ComicCraft
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env → GEMINI_API_KEY=...
python main.py
```

---

## How it works

1. You submit: story prompt, character name, setting, tone, art style  
2. **Gemini Flash** builds a 5-panel outline (title, scene, image prompt, caption)  
3. **Gemini Pro** expands each panel into narration + dialogue  
4. **Image generator** creates a panel illustration for each scene  
5. **Layout builder** binds image + text  
6. **Exporter** writes a PDF under `static/exports/`  
7. Preview page shows all panels + **Download PDF** button  

---

## Image modes

| Mode | Env value | Notes |
|------|-----------|--------|
| **Pillow** (default) | `IMAGE_MODE=pillow` | Fast stylized comic frames, no GPU, always works |
| **Diffusers** | `IMAGE_MODE=diffusers` | Local Stable Diffusion (`runwayml/stable-diffusion-v1-5`). Needs `torch`, `diffusers`, lots of RAM/GPU. First run downloads ~4GB model. |

To try Diffusers (optional):

```cmd
pip install torch diffusers transformers accelerate safetensors
```

Then set in `.env`:

```
IMAGE_MODE=diffusers
```

---

## API examples

**Form:** `POST /generate` (used by the website)

**JSON:**

```bash
curl -X POST http://127.0.0.1:8000/generate-comic/json ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"A brave fox in an enchanted forest\",\"character\":\"Felix\",\"setting\":\"forest\",\"tone\":\"funny\",\"art_style\":\"comic book\"}"
```

**Test image only:**

```
GET /test-image?prompt=a+hero+in+space+comic+style
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Activate venv, run `pip install -r requirements.txt` |
| Gemini errors / demo text | Set valid `GEMINI_API_KEY` in `.env`, restart |
| Slow generation | Normal with live Gemini; 5 panels take ~15–40s |
| Port in use | Change `PORT=8001` in `.env` |
| PDF missing images | Ensure generation finished; check `static/panels/` |

---

## Tech stack

- FastAPI + Uvicorn + Jinja2  
- Google Generative AI (`gemini-1.5-flash` / `gemini-1.5-pro`)  
- Pillow (default images) / optional Hugging Face Diffusers  
- FPDF2 for PDF export  

---

**ComicCraft** — turn a prompt into a comic in one click.
