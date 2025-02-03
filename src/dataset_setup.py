import pandas as pd
from datasets import Dataset
from transformers import DistilBertTokenizer

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"  # using local cache directory for models

tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)

def load_and_prepare_dataset(csv_path="dataset.csv"):
    # Load dataset from CSV file
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)
    return dataset

def tokenize_dataset(dataset):
    # Tokenize text using the DistilBERT tokenizer
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True)
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    # Remove the original text column if it exists to keep dataset compact
    if "text" in tokenized_dataset.column_names:
        tokenized_dataset = tokenized_dataset.remove_columns(["text"])
    return tokenized_dataset