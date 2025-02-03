import os
from transformers import DistilBertForSequenceClassification, Trainer, TrainingArguments, DistilBertTokenizer
from dataset_setup import load_and_prepare_dataset, tokenize_dataset

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
MODEL_DIR = "model/scam_detector"

def get_tokenizer_and_model():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    
    if os.path.exists(MODEL_DIR):
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    else:
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2, cache_dir=CACHE_DIR)
    return tokenizer, model

def train_model():
    tokenizer, model = get_tokenizer_and_model()
    
    if os.path.exists(MODEL_DIR):
        return model, tokenizer

    dataset = load_and_prepare_dataset(csv_path="dataset.csv")
    tokenized_dataset = tokenize_dataset(dataset)
    
    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="no",
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=5,
        save_strategy="epoch",
        logging_dir="./logs",
        logging_steps=10,
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )
    
    trainer.train()
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    
    return model, tokenizer

if __name__ == "__main__":
    train_model()