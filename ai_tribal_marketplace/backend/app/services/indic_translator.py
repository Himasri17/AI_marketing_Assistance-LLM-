from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

_MODEL = None
_TOKENIZER = None


def load_model():
    global _MODEL, _TOKENIZER

    if _MODEL is None:
        model_name = "ai4bharat/indictrans2-en-indic-dist-200M"

        _TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        _MODEL = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        _MODEL.eval()


def translate_konkani(text: str):
    load_model()

    tokenizer = _TOKENIZER
    model = _MODEL

    inputs = tokenizer(
        text,
        return_tensors="pt",
        src_lang="eng_Latn",
        tgt_lang="gom_Deva"
    )

    with torch.no_grad():
        generated = model.generate(
            **inputs,
            max_length=200,
            num_beams=4
        )

    output = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True
    )[0].strip()

    return output
