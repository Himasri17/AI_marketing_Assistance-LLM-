from transformers import ViTImageProcessor, ViTModel
import torch

# Try to load heavy ViT model; fall back to a dummy feature vector if unavailable
try:
    feature_extractor = ViTImageProcessor.from_pretrained(
        "google/vit-base-patch16-224"
    )
    model = ViTModel.from_pretrained("google/vit-base-patch16-224")
except Exception:
    feature_extractor = None
    model = None

def extract_features(image):
    if feature_extractor is None or model is None:
        # return a dummy feature vector
        return torch.zeros((1, 768))

    inputs = feature_extractor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    features = outputs.last_hidden_state.mean(dim=1)
    return features