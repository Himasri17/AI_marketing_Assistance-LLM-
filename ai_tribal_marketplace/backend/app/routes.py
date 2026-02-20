"""
routes.py
---------
Two generation endpoints:

  POST /generate/        — Creator mode (art name + description + translations)
  POST /generate/history — Scholar mode (art name + historical answer + translations)

Both:
  - Accept a multipart image upload
  - Call Claude for vision-based generation
  - Cache results in the DB (keyed on english text to avoid duplicate API calls)
  - Translate missing languages on demand
  - Return JSON immediately; DB writes happen as background tasks
"""

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session
from PIL import Image
import io
import asyncio
from typing import Literal

from .database import get_db
from .models import Product
from .services.text_generator import generate_description, generate_history
from .services.translator import translate

router = APIRouter()

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = {"hindi", "marathi", "bengali", "tamil", "telugu"}


def _parse_languages(languages: str) -> list[str]:
    """Split comma-separated language string and validate each entry."""
    langs = [l.strip().lower() for l in languages.split(",") if l.strip()]
    unknown = [l for l in langs if l not in SUPPORTED_LANGUAGES]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language(s): {unknown}. "
                   f"Supported: {sorted(SUPPORTED_LANGUAGES)}",
        )
    return langs


async def _read_image(file: UploadFile) -> Image.Image:
    """Read upload and return a PIL RGB image."""
    contents = await file.read()
    try:
        return Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=422, detail="Cannot open uploaded file as an image.")


async def _resolve_translations(
    english: str,
    requested_languages: list[str],
    db: Session,
) -> tuple[dict[str, str], "Product | None"]:
    """
    Look up the DB for cached translations, then translate any missing ones.
    Returns (translations_dict, existing_db_row_or_None).
    """
    existing = db.query(Product).filter(Product.english == english).first()
    cached: dict[str, str] = {}

    if existing:
        for lang in requested_languages:
            value = getattr(existing, lang, None)
            if value:
                cached[lang] = value

    missing = [l for l in requested_languages if l not in cached]

    loop = asyncio.get_event_loop()
    fresh: dict[str, str] = {}
    for lang in missing:
        translation = await loop.run_in_executor(None, translate, english, lang)
        fresh[lang] = translation

    return {**cached, **fresh}, existing


def _make_db_saver(
    db: Session,
    english: str,
    art_name: str,
    art_style: str,
    region: str,
    translations: dict[str, str],
    existing: "Product | None",
    question: str | None = None,
):
    """Return a zero-argument callable suitable for BackgroundTasks."""
    def _save():
        try:
            if existing:
                # Update any newly translated columns
                for lang, value in translations.items():
                    setattr(existing, lang, value)
                db.commit()
            else:
                product = Product(
                    english=english,
                    art_name=art_name,
                    art_style=art_style,
                    region=region,
                    question=question,
                    hindi=translations.get("hindi"),
                    marathi=translations.get("marathi"),
                    bengali=translations.get("bengali"),
                    tamil=translations.get("tamil"),
                    telugu=translations.get("telugu"),
                )
                db.add(product)
                db.commit()
        except Exception:
            db.rollback()
            raise
    return _save


# ---------------------------------------------------------------------------
# Endpoint 1: Creator — art name + description + translations
# ---------------------------------------------------------------------------

@router.post("/generate/")
async def generate(
    file: UploadFile = File(...),
    languages: str = Query(default="", description="Comma-separated: hindi,marathi,bengali,tamil,telugu"),
    length: Literal["short", "medium", "detailed"] = Query(default="medium"),
    audience: Literal["general", "buyer", "student", "children"] = Query(default="general"),
    tone: Literal["poetic", "informative", "storytelling", "academic"] = Query(default="poetic"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Creator mode.

    - Identifies the tribal art form
    - Generates: art_name, art_style, region, english description
    - Translates into requested languages
    - Caches in DB

    Returns:
    {
        "art_name": "...",
        "art_style": "...",
        "region": "...",
        "english": "...",
        "translations": { "hindi": "...", ... }
    }
    """
    try:
        requested_languages = _parse_languages(languages) if languages.strip() else []
        image = await _read_image(file)

        # --- Claude vision call ---
        ai_result = generate_description(image, length=length, audience=audience, tone=tone)
        english   = ai_result["english"]
        art_name  = ai_result.get("art_name", "Unknown Art")
        art_style = ai_result.get("art_style", "")
        region    = ai_result.get("region", "India")

        # --- Translations (cached + fresh) ---
        translations, existing = await _resolve_translations(english, requested_languages, db)

        # --- Persist to DB in background ---
        saver = _make_db_saver(db, english, art_name, art_style, region, translations, existing)
        if background_tasks:
            background_tasks.add_task(saver)
        else:
            saver()

        return {
            "art_name":     art_name,
            "art_style":    art_style,
            "region":       region,
            "english":      english,
            "translations": translations,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Endpoint 2: Scholar — art history + translations
# ---------------------------------------------------------------------------

@router.post("/generate/history")
async def generate_art_history(
    file: UploadFile = File(...),
    languages: str = Query(default="", description="Comma-separated: hindi,marathi,bengali,tamil,telugu"),
    question: str = Query(
        default="Tell me the history and origins of this art form.",
        description="The historical/cultural question to answer about the artwork.",
    ),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Scholar mode.

    - Identifies the tribal art form
    - Answers the provided historical/cultural question
    - Translates the answer into requested languages
    - Caches in DB (keyed on english answer text)

    Returns:
    {
        "art_name":  "...",
        "art_style": "...",
        "region":    "...",
        "question":  "...",
        "english":   "...",
        "translations": { "hindi": "...", ... }
    }
    """
    try:
        requested_languages = _parse_languages(languages) if languages.strip() else []
        image = await _read_image(file)

        # --- Claude vision call ---
        ai_result = generate_history(image, question=question)
        english   = ai_result["english"]
        art_name  = ai_result.get("art_name", "Unknown Art")
        art_style = ai_result.get("art_style", "")
        region    = ai_result.get("region", "India")
        q_text    = ai_result.get("question", question)

        # --- Translations ---
        translations, existing = await _resolve_translations(english, requested_languages, db)

        # --- Persist ---
        saver = _make_db_saver(db, english, art_name, art_style, region, translations, existing, question=q_text)
        if background_tasks:
            background_tasks.add_task(saver)
        else:
            saver()

        return {
            "art_name":     art_name,
            "art_style":    art_style,
            "region":       region,
            "question":     q_text,
            "english":      english,
            "translations": translations,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Endpoint 3: History list (GET) — retrieve past generations
# ---------------------------------------------------------------------------

@router.get("/history/")
def get_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Return past generation records from the DB, newest first.
    """
    products = (
        db.query(Product)
        .order_by(Product.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id":        p.id,
            "art_name":  getattr(p, "art_name", None),
            "art_style": getattr(p, "art_style", None),
            "region":    getattr(p, "region", None),
            "question":  getattr(p, "question", None),
            "english":   p.english,
            "hindi":     p.hindi,
            "marathi":   p.marathi,
            "bengali":   p.bengali,
            "tamil":     p.tamil,
            "telugu":    p.telugu,
        }
        for p in products
    ]