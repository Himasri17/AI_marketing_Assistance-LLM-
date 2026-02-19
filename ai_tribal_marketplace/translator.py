from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Choose model:
# Change "en-hi" / "en-mr" / "en-bn"
MODEL = "Helsinki-NLP/opus-mt-en-hi"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)

def translate(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    outputs = model.generate(**inputs, max_length=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
