"""
Model Training Pipeline with MLflow Integration

This module handles:
- Fine-tuning transformer models on labeled data
- Experiment tracking with MLflow
- Model evaluation and validation
- Model versioning and registry
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import mlflow
import mlflow.pytorch
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    EvalPrediction,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


LABEL_MAP = {
    "Left-Leaning": 0,
    "Center-Left": 1,
    "Centrist": 2,
    "Center-Right": 3,
    "Right-Leaning": 4,
}

LABEL_NAMES = list(LABEL_MAP.keys())


class BiasDataset(Dataset):
    """PyTorch Dataset for political bias classification."""
    
    def __init__(
        self,
        texts: List[str],
        labels: List[int],
        tokenizer,
        max_length: int = 512,
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


class BiasModelTrainer:
    """Train political bias classification models."""
    
    def __init__(self, config_path: str = "training/config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        # Setup MLflow
        mlflow.set_tracking_uri(self.config["mlflow"]["tracking_uri"])
        mlflow.set_experiment(self.config["mlflow"]["experiment_name"])
        
        # Setup device
        self.device = self._setup_device()
        logger.info(f"Using device: {self.device}")
    
    def _setup_device(self) -> str:
        """Setup compute device (CPU, CUDA, or MPS for Apple Silicon)."""
        device_config = self.config["hardware"]["device"]
        
        if device_config == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device_config
    
    def load_data(
        self,
        train_file: str,
        val_file: str,
        test_file: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        """Load training and validation data."""
        logger.info("Loading data...")
        
        train_df = pd.read_csv(train_file)
        val_df = pd.read_csv(val_file)
        test_df = pd.read_csv(test_file) if test_file else None
        
        logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df) if test_df is not None else 0}")
        
        return train_df, val_df, test_df
    
    def prepare_datasets(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        tokenizer,
    ) -> Tuple[BiasDataset, BiasDataset]:
        """Prepare PyTorch datasets."""
        logger.info("Preparing datasets...")
        
        # Combine title and summary (and content if available)
        def combine_text(row):
            parts = [str(row.get("title", ""))]
            if "summary" in row and pd.notna(row["summary"]):
                parts.append(str(row["summary"]))
            if "content" in row and pd.notna(row["content"]):
                parts.append(str(row["content"])[:2000])  # Limit content length
            return " ".join(parts)
        
        train_texts = train_df.apply(combine_text, axis=1).tolist()
        val_texts = val_df.apply(combine_text, axis=1).tolist()
        
        train_labels = [LABEL_MAP[label] for label in train_df["human_label"]]
        val_labels = [LABEL_MAP[label] for label in val_df["human_label"]]
        
        train_dataset = BiasDataset(train_texts, train_labels, tokenizer)
        val_dataset = BiasDataset(val_texts, val_labels, tokenizer)
        
        return train_dataset, val_dataset
    
    def compute_metrics(self, pred: EvalPrediction) -> Dict[str, float]:
        """Compute evaluation metrics."""
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        
        return {
            "accuracy": accuracy_score(labels, preds),
            "f1_macro": f1_score(labels, preds, average="macro"),
            "f1_weighted": f1_score(labels, preds, average="weighted"),
            "precision": precision_score(labels, preds, average="weighted"),
            "recall": recall_score(labels, preds, average="weighted"),
        }
    
    def train(
        self,
        train_file: str,
        val_file: str,
        model_name: Optional[str] = None,
        output_dir: str = "models/custom",
    ) -> Trainer:
        """
        Train a model and log to MLflow.
        
        Args:
            train_file: Path to training data CSV
            val_file: Path to validation data CSV
            model_name: Base model to fine-tune (default from config)
            output_dir: Directory to save model checkpoints
        """
        if model_name is None:
            model_name = self.config["model"]["custom"]["architecture"]
        
        logger.info(f"Training model: {model_name}")
        
        # Start MLflow run
        with mlflow.start_run() as run:
            # Log parameters
            mlflow.log_params({
                "model_name": model_name,
                "train_file": train_file,
                "val_file": val_file,
                "epochs": self.config["training"]["epochs"],
                "batch_size": self.config["training"]["batch_size"],
                "learning_rate": self.config["model"]["custom"]["learning_rate"],
            })
            
            # Load data
            train_df, val_df, _ = self.load_data(train_file, val_file)
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=5,
                problem_type="single_label_classification",
            )
            
            # Prepare datasets
            train_dataset, val_dataset = self.prepare_datasets(
                train_df, val_df, tokenizer
            )
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.config["training"]["epochs"],
                per_device_train_batch_size=self.config["training"]["batch_size"],
                per_device_eval_batch_size=self.config["training"]["batch_size"],
                learning_rate=self.config["model"]["custom"]["learning_rate"],
                warmup_steps=self.config["model"]["custom"]["warmup_steps"],
                weight_decay=self.config["model"]["custom"]["weight_decay"],
                logging_steps=self.config["training"]["logging_steps"],
                eval_steps=self.config["training"]["eval_steps"],
                save_steps=self.config["training"]["save_steps"],
                evaluation_strategy="steps",
                save_strategy="steps",
                load_best_model_at_end=True,
                metric_for_best_model="f1_macro",
                fp16=self.config["training"]["fp16"] and self.device == "cuda",
                gradient_accumulation_steps=self.config["training"]["gradient_accumulation_steps"],
                max_grad_norm=self.config["training"]["max_grad_norm"],
                report_to=["mlflow"],
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                compute_metrics=self.compute_metrics,
            )
            
            # Train
            logger.info("Starting training...")
            train_result = trainer.train()
            
            # Evaluate
            logger.info("Evaluating on validation set...")
            eval_result = trainer.evaluate()
            
            # Log metrics
            mlflow.log_metrics(eval_result)
            
            # Save model
            trainer.save_model(output_dir)
            tokenizer.save_pretrained(output_dir)
            
            # Log model to MLflow
            if self.config["mlflow"]["log_models"]:
                mlflow.pytorch.log_model(
                    model,
                    "model",
                    registered_model_name="political_bias_classifier",
                )
            
            # Generate and log classification report
            predictions = trainer.predict(val_dataset)
            preds = predictions.predictions.argmax(-1)
            labels = predictions.label_ids
            
            report = classification_report(
                labels,
                preds,
                target_names=LABEL_NAMES,
                output_dict=True,
            )
            
            logger.info(f"\nClassification Report:\n{classification_report(labels, preds, target_names=LABEL_NAMES)}")
            
            # Log confusion matrix
            cm = confusion_matrix(labels, preds)
            logger.info(f"\nConfusion Matrix:\n{cm}")
            
            # Save artifacts
            report_path = Path(output_dir) / "classification_report.txt"
            with open(report_path, "w") as f:
                f.write(classification_report(labels, preds, target_names=LABEL_NAMES))
            mlflow.log_artifact(report_path)
            
            logger.info(f"Training complete! Run ID: {run.info.run_id}")
            logger.info(f"Model saved to: {output_dir}")
            
            return trainer
    
    def evaluate_test_set(
        self,
        model_path: str,
        test_file: str,
    ) -> Dict[str, float]:
        """Evaluate a trained model on the test set."""
        logger.info(f"Evaluating model on test set: {test_file}")
        
        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # Load test data
        test_df = pd.read_csv(test_file)
        
        # Prepare dataset
        def combine_text(row):
            parts = [str(row.get("title", ""))]
            if "summary" in row and pd.notna(row["summary"]):
                parts.append(str(row["summary"]))
            if "content" in row and pd.notna(row["content"]):
                parts.append(str(row["content"])[:2000])
            return " ".join(parts)
        
        test_texts = test_df.apply(combine_text, axis=1).tolist()
        test_labels = [LABEL_MAP[label] for label in test_df["human_label"]]
        
        test_dataset = BiasDataset(test_texts, test_labels, tokenizer)
        
        # Evaluate
        trainer = Trainer(model=model, compute_metrics=self.compute_metrics)
        results = trainer.evaluate(test_dataset)
        
        logger.info(f"Test Results: {results}")
        return results


def main():
    """Example usage."""
    trainer = BiasModelTrainer()
    
    # Example: Train a new model
    # trainer.train(
    #     train_file="data/processed/train_20260216_120000.csv",
    #     val_file="data/processed/val_20260216_120000.csv",
    #     output_dir="models/custom_roberta",
    # )
    
    # Example: Evaluate on test set
    # trainer.evaluate_test_set(
    #     model_path="models/custom_roberta",
    #     test_file="data/processed/test_20260216_120000.csv",
    # )
    
    logger.info("Training pipeline ready!")


if __name__ == "__main__":
    main()
