from deep_translator import GoogleTranslator

# Map frontend language names → Google codes
LANGUAGE_CODES = {
    "hindi": "hi",
    "marathi": "mr",
    "bengali": "bn",
    "tamil": "ta",
    "telugu": "te",
}


def translate(text: str, language: str):
    if language not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported language: {language}")

    target_code = LANGUAGE_CODES[language]

    return GoogleTranslator(
        source="auto",
        target=target_code
    ).translate(text)


def batch_translate(text: str, languages: list):
    translations = {"english": text}

    for lang in languages:
        if lang in LANGUAGE_CODES:
            translations[lang] = translate(text, lang)

    return translations
