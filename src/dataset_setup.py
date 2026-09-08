"""Load the scam training dataset and tokenize it for DistilBERT."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Dataset

import config
from predict import get_tokenizer

logger = logging.getLogger(__name__)


def load_and_prepare_dataset(csv_path: str | Path | None = None) -> Dataset:
    """Load the labelled CSV (``text``,``label`` columns) into a HF Dataset."""
    path = Path(csv_path) if csv_path is not None else config.DATASET_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found at {path}")

    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("The dataset is empty.")
    if not {"text", "label"}.issubset(df.columns):
        raise ValueError("The dataset must contain 'text' and 'label' columns.")
    return Dataset.from_pandas(df)


def tokenize_dataset(dataset: Dataset, tokenizer: Any | None = None) -> Dataset:
    """Tokenize a ``text``/``label`` dataset, dropping the raw text column."""
    tok = tokenizer if tokenizer is not None else get_tokenizer()

    def tokenize_function(examples: dict[str, list[str]]) -> dict[str, list[list[int]]]:
        return tok(examples["text"], padding="max_length", truncation=True)

    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    if "text" in tokenized_dataset.column_names:
        tokenized_dataset = tokenized_dataset.remove_columns(["text"])
    return tokenized_dataset
