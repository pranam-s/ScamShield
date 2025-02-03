import pandas as pd
from datasets import Dataset
from transformers import DistilBertTokenizer

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"

tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)

def load_and_prepare_dataset(csv_path="dataset.csv"):
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)
    return dataset

def tokenize_dataset(dataset):
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True)
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    if "text" in tokenized_dataset.column_names:
        tokenized_dataset = tokenized_dataset.remove_columns(["text"])
    return tokenized_dataset