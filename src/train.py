"""Train (or retrain with user feedback) the DistilBERT scam detector."""

from __future__ import annotations

import logging
import math
import os
from functools import lru_cache
from typing import Any

import evaluate
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    Trainer,
    TrainingArguments,
    get_linear_schedule_with_warmup,
)

import config
import db
from dataset_setup import load_and_prepare_dataset, tokenize_dataset

logger = logging.getLogger(__name__)

EVAL_SPLIT_FRACTION = 0.1  # fraction of the dataset held out for evaluation


@lru_cache(maxsize=1)
def _accuracy_metric() -> Any:
    return evaluate.load("accuracy")


def compute_metrics(p: Any) -> dict[str, float]:
    metric = _accuracy_metric()
    predictions = np.argmax(p.predictions, axis=-1)
    return metric.compute(predictions=predictions, references=p.label_ids)


def get_tokenizer_and_model() -> tuple[DistilBertTokenizer, DistilBertForSequenceClassification]:
    tokenizer = DistilBertTokenizer.from_pretrained(
        config.MODEL_NAME, cache_dir=str(config.CACHE_DIR)
    )
    if os.path.exists(config.MODEL_DIR):
        model = DistilBertForSequenceClassification.from_pretrained(str(config.MODEL_DIR))
        logger.info("Loaded fine-tuned model from %s", config.MODEL_DIR)
    else:
        model = DistilBertForSequenceClassification.from_pretrained(
            config.MODEL_NAME, num_labels=2, cache_dir=str(config.CACHE_DIR)
        )
        logger.info("Loaded pre-trained model %s", config.MODEL_NAME)
    return tokenizer, model


def train_model(
    retrain: bool = False,
) -> tuple[DistilBertForSequenceClassification, DistilBertTokenizer, str]:
    """Train the scam detector, optionally folding in human feedback.

    With ``retrain=False`` and existing fine-tuned weights this is a no-op
    that just returns the saved model.
    """
    tokenizer, model = get_tokenizer_and_model()

    if not retrain and os.path.exists(config.MODEL_DIR):
        logger.info("Existing trained model found at %s; nothing to do.", config.MODEL_DIR)
        return model, tokenizer, str(config.MODEL_DIR)

    logger.info("Training / retraining model...")
    db.init_db()
    dataset = load_and_prepare_dataset()
    dataset = dataset.train_test_split(test_size=EVAL_SPLIT_FRACTION, seed=42)
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    if retrain:
        feedback_examples = db.load_feedback_data()
        if feedback_examples:
            logger.info("Loaded %d feedback records.", len(feedback_examples))
            initial_train_df = train_dataset.to_pandas()
            feedback_df = pd.DataFrame(feedback_examples)
            combined_df = pd.concat([initial_train_df, feedback_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=["text"])
            train_dataset = Dataset.from_pandas(combined_df)
            logger.info("Combined training dataset size: %d", len(train_dataset))
        else:
            logger.info("No feedback data found; retraining on the base dataset only.")

    tokenized_train_dataset = tokenize_dataset(train_dataset, tokenizer=tokenizer)
    tokenized_eval_dataset = tokenize_dataset(eval_dataset, tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=str(config.PROJECT_ROOT / "results"),
        eval_strategy="epoch",
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        save_strategy="epoch",
        logging_dir=str(config.PROJECT_ROOT / "logs"),
        logging_steps=10,
        report_to="none",
        learning_rate=2e-5,
        weight_decay=0.01,
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_args.learning_rate,
        weight_decay=training_args.weight_decay,
    )
    num_training_steps = math.ceil(
        len(tokenized_train_dataset)
        * training_args.num_train_epochs
        / training_args.per_device_train_batch_size
    )
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
        optimizers=(optimizer, scheduler),
    )

    trainer.train()
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    model.save_pretrained(str(config.MODEL_DIR))
    tokenizer.save_pretrained(str(config.MODEL_DIR))

    eval_metrics = trainer.evaluate(eval_dataset=tokenized_eval_dataset)
    accuracy = eval_metrics.get("eval_accuracy")
    with db.connect() as database:
        database.execute(
            """
            INSERT INTO model_metadata (model_name, dataset_version, training_epochs, number_labels, accuracy)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                config.MODEL_NAME,
                config.DATASET_VERSION,
                training_args.num_train_epochs,
                2,
                accuracy,
            ),
        )
        database.commit()

    logger.info("Model saved to %s", config.MODEL_DIR)
    return model, tokenizer, str(config.MODEL_DIR)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_model(retrain=False)
