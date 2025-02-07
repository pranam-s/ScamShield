import os
import sqlite3
import pandas as pd
from transformers import DistilBertForSequenceClassification, Trainer, TrainingArguments, DistilBertTokenizer
from dataset_setup import load_and_prepare_dataset, tokenize_dataset
from datasets import Dataset

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
MODEL_DIR = "model/scam_detector"
DATABASE_PATH = "scam_calls.db"  # Add database path
DATASET_VERSION = "1.0" #for model metadata

def get_tokenizer_and_model():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    if os.path.exists(MODEL_DIR):
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
        print(f"Loaded fine-tuned model from {MODEL_DIR}")
    else:
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2, cache_dir=CACHE_DIR)
        print(f"Loaded pre-trained model {MODEL_NAME}")
    return tokenizer, model

def load_feedback_data(db_path=DATABASE_PATH):
    """Loads data with user feedback from the database."""
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT full_transcription as text, user_feedback, final_status
                FROM call_records
                WHERE user_feedback IS NOT NULL
            """)
            feedback_data = cursor.fetchall()

            data = []
            for text, feedback, final_status in feedback_data:
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
    """Initializes the database (creates tables if they don't exist)."""
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
        # Add indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_id ON call_records (call_id)")

        db.commit()

def train_model(retrain=False):
    """Trains or retrains the model."""
    tokenizer, model = get_tokenizer_and_model()

    if not retrain and os.path.exists(MODEL_DIR):
        print("Loading existing trained model.")
        return model, tokenizer

    print("Training or retraining model...")

    # Initialize the database (ensure tables exist)
    init_db()

    # Load initial dataset
    dataset = load_and_prepare_dataset(csv_path="dataset.csv")

    if retrain:
        # Load feedback data
        feedback_df = load_feedback_data()
        if feedback_df is not None and not feedback_df.empty:
            print(f"Loaded {len(feedback_df)} feedback records.")
            # Combine initial dataset and feedback data
            initial_df = dataset.to_pandas()
            combined_df = pd.concat([initial_df, feedback_df], ignore_index=True)
            # Remove duplicates
            combined_df = combined_df.drop_duplicates(subset=['text'])
            dataset = Dataset.from_pandas(combined_df)
            print(f"Combined dataset size: {len(dataset)}")
        else:
            print("No feedback data found or loaded.")

    tokenized_dataset = tokenize_dataset(dataset)

    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="no",  # No evaluation during training.  Could add validation set.
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        save_strategy="epoch",
        logging_dir="./logs",
        logging_steps=10,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        # eval_dataset=tokenized_eval_dataset,  # Add if you have a separate evaluation set
        # compute_metrics=compute_metrics,  # Add if you want to compute metrics during training
    )

    trainer.train()

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)

    # Update model metadata
    with sqlite3.connect(DATABASE_PATH) as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO model_metadata (model_name, dataset_version, training_epochs, number_labels)
            VALUES (?, ?, ?, ?)
        """, (MODEL_NAME, DATASET_VERSION, training_args.num_train_epochs, 2))  # Adjust as needed
        db.commit()

    print(f"Model saved to {MODEL_DIR}")
    return model, tokenizer

if __name__ == "__main__":
    train_model(retrain=True)  # Example of retraining