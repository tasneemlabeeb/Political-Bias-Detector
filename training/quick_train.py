#!/usr/bin/env python3
"""
Quick Model Training Script

Train a RoBERTa model for political bias classification using the enhanced dataset.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score, f1_score, classification_report
from datasets import Dataset
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Label mapping
LABEL_MAP = {
    "Left-Leaning": 0,
    "Center-Left": 1,
    "Centrist": 2,
    "Center-Right": 3,
    "Right-Leaning": 4,
}

ID_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}


def find_latest_dataset():
    """Find the most recent enhanced dataset."""
    processed_dir = Path("data/processed")
    train_files = sorted(processed_dir.glob("train_enhanced_*.csv"))
    val_files = sorted(processed_dir.glob("val_enhanced_*.csv"))
    test_files = sorted(processed_dir.glob("test_enhanced_*.csv"))
    
    if not train_files or not val_files:
        raise FileNotFoundError("No enhanced dataset found! Run download_kaggle_dataset.py first.")
    
    return str(train_files[-1]), str(val_files[-1]), str(test_files[-1]) if test_files else None


def load_and_prepare_data(train_path, val_path, test_path=None):
    """Load CSV files and prepare for training."""
    logger.info(f"Loading training data from: {train_path}")
    train_df = pd.read_csv(train_path)
    
    logger.info(f"Loading validation data from: {val_path}")
    val_df = pd.read_csv(val_path)
    
    test_df = None
    if test_path:
        logger.info(f"Loading test data from: {test_path}")
        test_df = pd.read_csv(test_path)
    
    # Use 'text' and 'label_id' columns
    def prepare_dataset(df):
        return Dataset.from_dict({
            'text': df['text'].tolist(),
            'label': df['label_id'].tolist()
        })
    
    train_dataset = prepare_dataset(train_df)
    val_dataset = prepare_dataset(val_df)
    test_dataset = prepare_dataset(test_df) if test_df is not None else None
    
    logger.info(f"Dataset sizes - Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset) if test_dataset else 0}")
    
    # Show class distribution
    logger.info("\nTraining set distribution:")
    logger.info(train_df['label'].value_counts().to_string())
    
    return train_dataset, val_dataset, test_dataset


def tokenize_data(dataset, tokenizer, max_length=512):
    """Tokenize the dataset."""
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=max_length
        )
    
    return dataset.map(tokenize_function, batched=True)


def compute_metrics(pred):
    """Compute evaluation metrics."""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='weighted')
    
    return {
        'accuracy': acc,
        'f1': f1,
    }


def train_model(
    model_name="roberta-base",
    output_dir="models/custom_bias_detector",
    num_epochs=3,
    batch_size=16,
    learning_rate=2e-5,
):
    """Train the model."""
    
    logger.info("="*70)
    logger.info("Political Bias Detector - Model Training")
    logger.info("="*70)
    
    # Find datasets
    logger.info("\n📂 Step 1: Loading datasets...")
    train_path, val_path, test_path = find_latest_dataset()
    train_dataset, val_dataset, test_dataset = load_and_prepare_data(train_path, val_path, test_path)
    
    # Determine number of labels from data
    unique_labels = sorted(set(train_dataset['label']))
    num_labels = len(unique_labels)
    logger.info(f"\nNumber of classes: {num_labels}")
    logger.info(f"Label IDs in dataset: {unique_labels}")
    
    # Create label mapping for only the labels that exist in dataset
    actual_id2label = {i: ID_TO_LABEL[i] for i in unique_labels if i in ID_TO_LABEL}
    actual_label2id = {v: k for k, v in actual_id2label.items()}
    
    logger.info(f"ID to Label mapping: {actual_id2label}")
    
    # Load tokenizer and model
    logger.info(f"\n🤖 Step 2: Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        id2label=actual_id2label,
        label2id=actual_label2id
    )
    
    # Tokenize datasets
    logger.info("\n🔤 Step 3: Tokenizing datasets...")
    train_dataset = tokenize_data(train_dataset, tokenizer)
    val_dataset = tokenize_data(val_dataset, tokenizer)
    if test_dataset:
        test_dataset = tokenize_data(test_dataset, tokenizer)
    
    # Training arguments
    logger.info("\n⚙️  Step 4: Configuring training...")
    
    # Only use fp16 on CUDA GPUs, not on MPS (Apple Silicon) or CPU
    use_fp16 = torch.cuda.is_available()
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=f"{output_dir}/logs",
        logging_steps=100,
        save_total_limit=2,
        fp16=use_fp16,
        report_to="none",  # Disable wandb/tensorboard
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )
    
    # Train
    logger.info("\n🚀 Step 5: Training model...")
    logger.info(f"   Epochs: {num_epochs}")
    logger.info(f"   Batch size: {batch_size}")
    logger.info(f"   Learning rate: {learning_rate}")
    logger.info("")
    
    trainer.train()
    
    # Evaluate on validation
    logger.info("\n📊 Step 6: Evaluating on validation set...")
    val_results = trainer.evaluate()
    logger.info(f"Validation Results: {val_results}")
    
    # Evaluate on test if available
    if test_dataset:
        logger.info("\n📊 Step 7: Evaluating on test set...")
        test_results = trainer.evaluate(test_dataset)
        logger.info(f"Test Results: {test_results}")
        
        # Detailed classification report
        predictions = trainer.predict(test_dataset)
        preds = predictions.predictions.argmax(-1)
        labels = predictions.label_ids
        
        logger.info("\n📋 Classification Report:")
        report = classification_report(
            labels,
            preds,
            target_names=[actual_id2label[i] for i in sorted(actual_id2label.keys())],
            zero_division=0
        )
        logger.info(f"\n{report}")
    
    # Save final model
    logger.info(f"\n💾 Step 8: Saving model to: {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    logger.info("\n" + "="*70)
    logger.info("✅ Training complete!")
    logger.info(f"\nModel saved to: {output_dir}")
    logger.info("\n🎯 Next steps:")
    logger.info("   1. Update bias_classifier.py to use your trained model")
    logger.info("   2. Test the model in the Streamlit app")
    logger.info("="*70)
    
    return trainer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train political bias classification model")
    parser.add_argument("--model", default="roberta-base", help="Base model to fine-tune")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Training batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--output", default="models/custom_bias_detector", help="Output directory")
    
    args = parser.parse_args()
    
    train_model(
        model_name=args.model,
        output_dir=args.output,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )
