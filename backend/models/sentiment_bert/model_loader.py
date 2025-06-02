from transformers import BertTokenizer, BertForSequenceClassification
import torch

MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

def load_model():
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model