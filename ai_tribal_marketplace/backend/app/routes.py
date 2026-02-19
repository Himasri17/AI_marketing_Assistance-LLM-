from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from PIL import Image
import io
import asyncio

from .database import get_db
from .models import Product
from .services.image_captioner import generate_description
from .services.translator import translate

router = APIRouter()

@router.post("/generate/")
async def generate(
    file: UploadFile = File(...),
    languages: str = "hindi",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    try:
        # -----------------------------------
        # 1️⃣ Read image
        # -----------------------------------
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # -----------------------------------
        # 2️⃣ Generate English caption
        # -----------------------------------
        english = generate_description(image)

        requested_languages = [lang.strip() for lang in languages.split(",")]

        # -----------------------------------
        # 3️⃣ Check DB cache
        # -----------------------------------
        existing = db.query(Product).filter(Product.english == english).first()

        response_translations = {}

        if existing:
            for lang in requested_languages:
                value = getattr(existing, lang, None)
                if value:
                    response_translations[lang] = value

        # -----------------------------------
        # 4️⃣ Translate missing languages
        # -----------------------------------
        missing_languages = [
            lang for lang in requested_languages
            if lang not in response_translations
        ]

        loop = asyncio.get_event_loop()

        for lang in missing_languages:
            translation = await loop.run_in_executor(
                None,
                translate,
                english,
                lang
            )
            response_translations[lang] = translation

        # -----------------------------------
        # 5️⃣ Save to DB (update or insert)
        # -----------------------------------
        def save_to_db():
            if existing:
                for lang, value in response_translations.items():
                    setattr(existing, lang, value)
                db.commit()
            else:
                product = Product(
                    english=english,
                    hindi=response_translations.get("hindi"),
                    marathi=response_translations.get("marathi"),
                    bengali=response_translations.get("bengali"),
                    tamil=response_translations.get("tamil"),
                    telugu=response_translations.get("telugu"),
                )
                db.add(product)
                db.commit()

        if background_tasks:
            background_tasks.add_task(save_to_db)
        else:
            save_to_db()

        # -----------------------------------
        # 6️⃣ Return response
        # -----------------------------------
        return {
            "english": english,
            "translations": response_translations
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating translation: {str(e)}"
        )
