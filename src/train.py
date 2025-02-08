import os
import sqlite3
import pandas as pd
import numpy as np
from transformers import DistilBertForSequenceClassification, Trainer, TrainingArguments, DistilBertTokenizer, get_linear_schedule_with_warmup
from dataset_setup import load_and_prepare_dataset, tokenize_dataset
from datasets import Dataset
import evaluate
import torch

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
MODEL_DIR = "model/scam_detector"
DATABASE_PATH = "scam_calls.db"
DATASET_VERSION = "1.0"
EVAL_DATASET_SIZE = 0.1  # Fraction of dataset to use for evaluation

def get_tokenizer_and_model():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    if os.path.exists(MODEL_DIR):
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
        print(f"Loaded fine-tuned model from {MODEL_DIR}")
    else:
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2, cache_dir=CACHE_DIR)
        print(f"Loaded pre-trained model {MODEL_NAME}")
    return tokenizer, model

def compute_metrics(p):
    metric = evaluate.load("accuracy")
    predictions = np.argmax(p.predictions, axis=-1)
    return metric.compute(predictions=predictions, references=p.label_ids)

def load_feedback_data(db_path=DATABASE_PATH):
    try:
        with sqlite3.connect(db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute("""
                SELECT full_transcription as text, user_feedback, final_status
                FROM call_records
                WHERE user_feedback IS NOT NULL
            """)
            feedback_data = cursor.fetchall()
            data = []
            for row in feedback_data:
                text, feedback, final_status = row["text"], row["user_feedback"], row["final_status"]
                if feedback == "correct":
                    label = 1 if final_status == "Scam" else 0
                elif feedback == "incorrect":
                    label = 0 if final_status == "Scam" else 1
                else:
                    continue
                data.append({"text": text, "label": label})
            if not data:
                return None
            df = pd.DataFrame(data)
            return df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error loading feedback data: {e}")
        return None

def init_db():
    with sqlite3.connect(DATABASE_PATH) as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_records (
                call_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                duration REAL,
                caller_number TEXT,
                full_transcription TEXT,
                user_feedback TEXT,
                final_status TEXT,
                model_version_used TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metadata (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                training_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                dataset_version TEXT,
                accuracy REAL,
                training_epochs INTEGER,
                number_labels INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_id ON call_records (call_id)")
        db.commit()

def train_model(retrain=False):
    """Trains or retrains the model with optimizations."""
    tokenizer, model = get_tokenizer_and_model()

    if not retrain and os.path.exists(MODEL_DIR):
        print("Loading existing trained model.")
        return model, tokenizer, MODEL_DIR

    print("Training or retraining model...")
    init_db()
    dataset = load_and_prepare_dataset(csv_path="dataset.csv")
    dataset = dataset.train_test_split(test_size=EVAL_DATASET_SIZE, seed=42)
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    if retrain:
        feedback_df = load_feedback_data()
        if feedback_df is not None and not feedback_df.empty:
            print(f"Loaded {len(feedback_df)} feedback records.")
            initial_train_df = train_dataset.to_pandas()
            combined_train_df = pd.concat([initial_train_df, feedback_df], ignore_index=True)
            combined_train_df = combined_train_df.drop_duplicates(subset=['text'])
            train_dataset = Dataset.from_pandas(combined_train_df)
            print(f"Combined training dataset size: {len(train_dataset)}")
        else:
            print("No feedback data found or loaded.")

    tokenized_train_dataset = tokenize_dataset(train_dataset)
    tokenized_eval_dataset = tokenize_dataset(eval_dataset)

    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        save_strategy="epoch",
        logging_dir="./logs",
        logging_steps=10,
        report_to="none",
        learning_rate=2e-5,
        weight_decay=0.01,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=training_args.learning_rate, weight_decay=training_args.weight_decay)
    num_training_steps = (len(tokenized_train_dataset) * training_args.num_train_epochs) // training_args.per_device_train_batch_size
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train_dataset,
        eval_dataset=tokenized_eval_dataset,
        compute_metrics=compute_metrics,
        optimizers=(optimizer, scheduler)
    )

    trainer.train()
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)

    with sqlite3.connect(DATABASE_PATH) as db:
        cursor = db.cursor()
        eval_metrics = trainer.evaluate(eval_dataset=tokenized_eval_dataset)
        accuracy = eval_metrics.get("eval_accuracy")
        cursor.execute("""
            INSERT INTO model_metadata (model_name, dataset_version, training_epochs, number_labels, accuracy)
            VALUES (?, ?, ?, ?, ?)
        """, (MODEL_NAME, DATASET_VERSION, training_args.num_train_epochs, 2, accuracy))
        db.commit()

    print(f"Model saved to {MODEL_DIR}")
    return model, tokenizer, MODEL_DIR

if __name__ == "__main__":
    train_model(retrain=False)