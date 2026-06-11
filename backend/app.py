"""
MaxiMots — Maximo MAS 9 Translation Studio by maxTeam
=====================================================
Web app to manage translations for IBM Maximo MAS 9 objects.
- Serves the MaxiMots frontend (templates/index.html)
- Uploads and parses MXLoader Excel exports
- Detects missing translations across language columns
- Auto-translates via Google Translate (deep-translator) with manual override
- Exports back to MXLoader-compatible styled Excel
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from mxloader_parser import MXLoaderParser
from translator import TranslationEngine

app = FastAPI(title="MaxiMots — Translation Studio by maxTeam", version="2.0.0")

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# In-memory session store: session_id -> { parser, translations, filename }
sessions: dict = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload an MXLoader Excel sheet and parse it."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Only .xlsx/.xls files are supported")

    session_id = str(uuid.uuid4())[:8]
    filepath = UPLOAD_DIR / f"{session_id}_{file.filename}"

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    parser = MXLoaderParser(str(filepath))
    parse_result = parser.parse()

    sessions[session_id] = {
        "parser": parser,
        "filepath": str(filepath),
        "filename": file.filename,
        "translations": parse_result["rows"],
        "sheets": parse_result["sheets"],
        "languages": parse_result["languages"],
        "source_lang": parse_result["source_lang"],
        "id_columns": parse_result["id_columns"],
    }

    return {
        "session_id": session_id,
        "filename": file.filename,
        "sheets": parse_result["sheets"],
        "languages": parse_result["languages"],
        "source_lang": parse_result["source_lang"],
        "total_rows": len(parse_result["rows"]),
        "missing_count": sum(
            1 for r in parse_result["rows"]
            for lang in parse_result["languages"]
            if lang != parse_result["source_lang"] and not r["translations"].get(lang)
        ),
    }


@app.get("/session/{session_id}/rows")
async def get_rows(
    session_id: str,
    sheet: Optional[str] = None,
    filter: Optional[str] = None,
    target_lang: Optional[str] = None,
):
    """Get translation rows for a session, optionally filtered."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    data = sessions[session_id]
    rows = data["translations"]
    source_lang = data["source_lang"]

    if sheet:
        rows = [r for r in rows if r["sheet"] == sheet]

    if filter == "missing" and target_lang:
        rows = [r for r in rows if not r["translations"].get(target_lang)]
    elif filter == "translated" and target_lang:
        rows = [r for r in rows if r["translations"].get(target_lang)]

    return {
        "rows": rows,
        "total": len(rows),
        "languages": data["languages"],
        "source_lang": source_lang,
    }


@app.post("/session/{session_id}/auto-translate")
async def auto_translate(
    session_id: str,
    target_lang: str = Form(...),
    source_lang: Optional[str] = Form(None),
    provider: str = Form("google"),
    row_indices: Optional[str] = Form(None),
):
    """Auto-translate missing entries using external API."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    data = sessions[session_id]
    src = source_lang or data["source_lang"]
    rows = data["translations"]

    engine = TranslationEngine(provider=provider)

    if row_indices and row_indices != "all":
        indices = [int(i) for i in row_indices.split(",")]
    else:
        indices = list(range(len(rows)))

    translated_count = 0
    errors = []

    for idx in indices:
        if idx >= len(rows):
            continue
        row = rows[idx]
        source_text = row["translations"].get(src, "")
        if not source_text:
            continue
        if row["translations"].get(target_lang):
            continue

        try:
            result = engine.translate(source_text, src, target_lang)
            row["translations"][target_lang] = result
            row["auto_translated"] = row.get("auto_translated", {})
            row["auto_translated"][target_lang] = True
            translated_count += 1
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    return {
        "translated_count": translated_count,
        "errors": errors,
    }


@app.post("/session/{session_id}/manual-update")
async def manual_update(
    session_id: str,
    row_index: int = Form(...),
    lang: str = Form(...),
    value: str = Form(...),
):
    """Manually set a translation value."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    data = sessions[session_id]
    rows = data["translations"]

    if row_index >= len(rows):
        raise HTTPException(400, "Invalid row index")

    rows[row_index]["translations"][lang] = value
    rows[row_index]["auto_translated"] = rows[row_index].get("auto_translated", {})
    rows[row_index]["auto_translated"][lang] = False

    return {"ok": True}


@app.post("/session/{session_id}/export")
async def export_file(session_id: str):
    """Export the updated translations back to MXLoader-compatible Excel."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    data = sessions[session_id]
    parser = data["parser"]

    export_path = EXPORT_DIR / f"{session_id}_translated_{data['filename']}"
    parser.export(data["translations"], str(export_path))

    return FileResponse(
        str(export_path),
        filename=f"translated_{data['filename']}",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class TranslateItem(BaseModel):
    text: str
    target: str  # Maximo language code, e.g. "FR"


class TranslateRequest(BaseModel):
    items: list[TranslateItem]
    source: str = "EN"


@app.post("/translate")
async def translate_direct(req: TranslateRequest):
    """Direct batch translation used by the MaxiMots frontend auto-translate."""
    engine = TranslationEngine(provider="google")
    results = []
    errors = []
    for i, item in enumerate(req.items):
        try:
            results.append(engine.translate(item.text, req.source, item.target))
        except Exception as e:
            results.append(None)
            errors.append({"index": i, "error": str(e)})
    return {"results": results, "errors": errors}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the maxTeam logo embedded in the frontend as favicon."""
    import base64, re
    html_path = BASE_DIR / "templates" / "index.html"
    m = re.search(r'href="data:image/png;base64,([^"]+)"', html_path.read_text(encoding="utf-8"))
    if not m:
        raise HTTPException(404, "No favicon")
    b64 = m.group(1)
    data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
    media = "image/jpeg" if data[:2] == b"\xff\xd8" else "image/png"
    from fastapi import Response
    return Response(content=data, media_type=media)


@app.get("/supported-languages")
async def supported_languages():
    """Return list of supported language codes for translation."""
    engine = TranslationEngine()
    return engine.get_supported_languages()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
