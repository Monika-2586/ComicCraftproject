# 🎨 Comic Craft

**AI comic story creator powered by Google Gemini models.**
Type a short idea, and Comic Craft writes a multi-panel script, draws every panel, adds narration boxes and speech bubbles, and exports a finished comic as PNG or PDF.

## How it works

```
Your idea ──► Gemini text model ──► Structured script (JSON)
                                         │
                                         ▼
                      Gemini image model draws each panel
                      (character descriptions + previous panel
                       as reference keep faces consistent)
                                         │
                                         ▼
                  Pillow adds captions + speech bubbles, builds pages
                                         │
                                         ▼
                               PNG pages / PDF download
```

1. **Story stage** – a Gemini text model returns a validated JSON script (title, characters with fixed looks, panels with scene, caption and dialogue).
2. **Art stage** – a Gemini image model draws each panel. Character descriptions are repeated in every prompt and the previous panel is attached as a reference so characters stay consistent.
3. **Layout stage** – Pillow overlays text on the art (AI-drawn lettering is often garbled) and arranges panels into pages.

## Features

- Idea → full comic in two clicks
- Choose genre, tone, art style and number of panels (2–8)
- Edit the generated script before drawing
- Consistent characters across panels
- Resilient: retries on temporary API errors; a failed panel shows a placeholder instead of crashing
- Download pages as PNG or the whole comic as PDF

## Tech stack

Python 3.10+ · Streamlit · `google-genai` SDK · Pydantic · Pillow

## Setup

```bash
git clone https://github.com/<your-username>/comic-craft.git
cd comic-craft

python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env      # Windows: copy .env.example .env
# open .env and paste your Gemini API key
```

Get a free API key at <https://aistudio.google.com/apikey>.

## Run

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually <http://localhost:8501>).

## Configuration

| Setting | Where | Default |
|---|---|---|
| `GEMINI_API_KEY` | `.env` or sidebar | – (required) |
| Story model | sidebar or `COMICCRAFT_TEXT_MODEL` | `gemini-2.5-flash` |
| Image model | sidebar or `COMICCRAFT_IMAGE_MODEL` | `gemini-2.5-flash-image` |

Gemini model names change over time. If a model is retired, enter the current name from the [Gemini API docs](https://ai.google.dev/gemini-api/docs/models) in the sidebar – no code change needed.

## Run the tests

```bash
python -m unittest discover -s tests -t . -v
```

The tests cover the layout and configuration code and need no API key.

## Project structure

```
comic-craft/
├── app.py                  # Streamlit user interface
├── comiccraft/
│   ├── config.py           # settings, model names, API key loading
│   ├── story.py            # Gemini story generation (structured JSON)
│   ├── images.py           # Gemini panel image generation
│   ├── layout.py           # Pillow captions, bubbles, pages, PNG/PDF export
│   └── utils.py            # retry with exponential backoff
├── tests/                  # offline unit tests
├── requirements.txt
├── .env.example            # copy to .env (never commit .env)
└── README.md
```

## Push this project to GitHub

1. Create an **empty** repository on <https://github.com/new> named `comic-craft` (no README, no .gitignore).
2. In the project folder:

```bash
git init
git add .
git commit -m "Initial commit: Comic Craft AI comic creator"
git branch -M main
git remote add origin https://github.com/<your-username>/comic-craft.git
git push -u origin main
```

> ⚠️ Never commit your real API key. `.env` is already listed in `.gitignore`. If a key is ever pushed by mistake, delete it in Google AI Studio and create a new one.

## Limitations

- AI images can contain mistakes; character consistency is good but not perfect.
- Generation speed and cost depend on your Gemini API plan and quota.
- Text is rendered in English-friendly fonts; other scripts need a suitable font in `layout.py`.

## Future ideas

- Custom page layouts and speech-bubble tails
- Regenerate a single panel
- Multi-language comics with Unicode fonts
- Save and reload projects

## License

MIT – see [LICENSE](LICENSE).
