from .model_loader import load_model
import torch
import torch.nn.functional as F

tokenizer, model = load_model()

def predict_sentiment(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1).squeeze().tolist()

    # Adjust labels if using a model with 5-point output like nlptown
    label = probs.index(max(probs)) + 1  # 1 to 5 rating
    return {
        "rating": label,
        "confidence": max(probs),
        "probabilities": probs
    }