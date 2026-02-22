from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Literal
import asyncio
import tempfile
import os
from contextlib import asynccontextmanager

from .database import get_db
from .models import Product
from .services.text_generator import generate_description, generate_history
from .services.translator import translate

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = {"hindi", "marathi", "bengali", "tamil", "telugu"}

OLLAMA_TIMEOUT_SECONDS = 90


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_languages(languages: str) -> list[str]:
    langs = [l.strip().lower() for l in languages.split(",") if l.strip()]
    unknown = [l for l in langs if l not in SUPPORTED_LANGUAGES]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language(s): {unknown}. "
                   f"Supported: {sorted(SUPPORTED_LANGUAGES)}",
        )
    return langs


@asynccontextmanager
async def temp_image_file(upload: UploadFile):
    """
    Safely save uploaded image to a temp file and ensure cleanup.
    """
    contents = await upload.read()
    suffix = os.path.splitext(upload.filename)[1] or ".jpg"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(contents)
        tmp.close()
        yield tmp.name
    finally:
        try:
            os.remove(tmp.name)
        except FileNotFoundError:
            pass


async def run_with_timeout(func, timeout: int = OLLAMA_TIMEOUT_SECONDS):
    """
    Run blocking AI call in threadpool with timeout.
    """
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, func),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="AI model timed out. Please try again.",
        )


async def _resolve_translations(
    english: str,
    requested_languages: list[str],
    db: Session,
):
    existing = db.query(Product).filter(Product.english == english).first()
    cached = {}

    if existing:
        for lang in requested_languages:
            value = getattr(existing, lang, None)
            if value:
                cached[lang] = value

    missing = [l for l in requested_languages if l not in cached]

    loop = asyncio.get_event_loop()
    fresh = {}
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
    def _save():
        try:
            if existing:
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
# Endpoint 1: Creator Mode
# ---------------------------------------------------------------------------

@router.post("/generate/")
async def generate(
    file: UploadFile = File(...),
    languages: str = Query(default=""),
    length: Literal["short", "medium", "detailed"] = Query(default="medium"),
    audience: Literal["general", "buyer", "student", "children"] = Query(default="general"),
    tone: Literal["poetic", "informative", "storytelling", "academic"] = Query(default="poetic"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    try:
        requested_languages = _parse_languages(languages) if languages.strip() else []

        async with temp_image_file(file) as image_path:

            ai_result = await run_with_timeout(
                lambda: generate_description(
                    image_path,
                    length=length,
                    audience=audience,
                    tone=tone,
                )
            )

        english   = ai_result["english"]
        art_name  = ai_result.get("art_name", "Unknown Art")
        art_style = ai_result.get("art_style", "")
        region    = ai_result.get("region", "India")

        translations, existing = await _resolve_translations(
            english, requested_languages, db
        )

        saver = _make_db_saver(
            db, english, art_name, art_style, region, translations, existing
        )

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
# Endpoint 2: Scholar Mode
# ---------------------------------------------------------------------------

@router.post("/generate/history")
async def generate_art_history(
    file: UploadFile = File(...),
    languages: str = Query(default=""),
    question: str = Query(
        default="Tell me the history and origins of this art form.",
    ),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    try:
        requested_languages = _parse_languages(languages) if languages.strip() else []

        async with temp_image_file(file) as image_path:

            ai_result = await run_with_timeout(
                lambda: generate_history(image_path, question=question)
            )

        english   = ai_result["english"]
        art_name  = ai_result.get("art_name", "Unknown Art")
        art_style = ai_result.get("art_style", "")
        region    = ai_result.get("region", "India")
        q_text    = ai_result.get("question", question)

        translations, existing = await _resolve_translations(
            english, requested_languages, db
        )

        saver = _make_db_saver(
            db, english, art_name, art_style, region, translations, existing, question=q_text
        )

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
# Endpoint 3: History List
# ---------------------------------------------------------------------------

@router.get("/history/")
def get_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
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
            "art_name":  p.art_name,
            "art_style": p.art_style,
            "region":    p.region,
            "question":  p.question,
            "english":   p.english,
            "hindi":     p.hindi,
            "marathi":   p.marathi,
            "bengali":   p.bengali,
            "tamil":     p.tamil,
            "telugu":    p.telugu,
        }
        for p in products
    ]