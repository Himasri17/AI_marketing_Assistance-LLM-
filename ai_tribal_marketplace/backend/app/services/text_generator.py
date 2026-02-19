from transformers import pipeline

# Use a text generation pipeline
try:
    generator = pipeline('text-generation', model='gpt2')
except Exception:
    generator = None

def generate_description(features):
    if generator is None:
        return "Beautiful handcrafted tribal art product with unique cultural significance."

    prompt = "Generate a marketing description for a tribal art product: "
    result = generator(prompt, max_length=50, num_return_sequences=1)
    return result[0]['generated_text'].replace(prompt, "").strip()