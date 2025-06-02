# backend/services/retrain_model.py

import mlflow
import torch
import logging
from datetime import datetime
from backend.database.connection import db_pool
from backend.api.utils.notification import send_telegram_alert, send_slack_alert, send_email_alert
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# Logger
logger = logging.getLogger("retrain")
logging.basicConfig(level=logging.INFO)

# Constants
MODEL_NAME = "bert-base-uncased"
MIN_DATA_THRESHOLD = 100  # Minimum number of new samples before retraining

async def fetch_labeled_data():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT content, sentiment
            FROM reviews
            WHERE sentiment IS NOT NULL
        """)
        return [{"text": r["content"], "label": label_to_id(r["sentiment"])} for r in rows]

def label_to_id(label: str) -> int:
    mapping = {"negative": 0, "neutral": 1, "positive": 2}
    return mapping.get(label.lower(), 1)

def tokenize_function(example, tokenizer):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=128)

def retrain_sentiment_model():
    try:
        logger.info("🔁 Starting retraining pipeline...")
        
        # Step 1: Load and check data
        import asyncio
        labeled_data = asyncio.run(fetch_labeled_data())
        logger.info(f"📦 Fetched {len(labeled_data)} labeled samples")

        if len(labeled_data) < MIN_DATA_THRESHOLD:
            logger.info("⏸ Not enough data to retrain.")
            return

        # Step 2: Tokenize
        tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
        tokenized_dataset = Dataset.from_list(labeled_data).map(lambda x: tokenize_function(x, tokenizer), batched=True)

        # Step 3: Initialize model
        model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

        # Step 4: Setup MLflow
        mlflow.set_experiment("SentimentRetrain")
        with mlflow.start_run(run_name=f"retrain_{datetime.now().isoformat()}"):
            mlflow.log_param("model", MODEL_NAME)
            mlflow.log_param("training_size", len(labeled_data))

            training_args = TrainingArguments(
                output_dir="./models/sentiment_bert/retrained",
                num_train_epochs=2,
                per_device_train_batch_size=16,
                logging_steps=10,
                save_strategy="no"
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset
            )

            trainer.train()

            # Optional: Save model locally or to remote storage
            model.save_pretrained("./models/sentiment_bert/retrained")
            tokenizer.save_pretrained("./models/sentiment_bert/retrained")

            mlflow.log_artifacts("./models/sentiment_bert/retrained", artifact_path="model")

            logger.info("✅ Retraining complete and model saved.")
            logger.info("✅ Retraining complete and model saved.")
            send_telegram_alert("✅ Sentiment model retrained successfully.")
            send_slack_alert("✅ Sentiment model retrained successfully.")
            send_email_alert(
                subject="ML Retrain ✅",
                body="The sentiment model was retrained and saved successfully.",
                to="you@example.com"
            )
    except Exception as e:
        logger.error(f"❌ Retraining failed: {str(e)}")
        send_telegram_alert(f"❌ Retraining failed: {str(e)}")
        send_slack_alert(f"❌ Retraining failed: {str(e)}")
        send_email_alert(
            subject="ML Retrain ❌ FAILED",
            body=f"Retraining error: {str(e)}",
            to="you@example.com"
        )
        raise