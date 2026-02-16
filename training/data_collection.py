"""
Data Collection & Preparation Pipeline for Model Training

This module handles:
- Collecting articles from the database
- Exporting data for labeling
- Processing labeled data
- Creating train/val/test splits
"""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Collect and prepare data for model training."""
    
    def __init__(self, config_path: str = "training/config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.raw_dir = Path(self.config["data"]["raw_data_dir"])
        self.processed_dir = Path(self.config["data"]["processed_data_dir"])
        self.labeling_dir = Path(self.config["data"]["labeling_dir"])
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.labeling_dir.mkdir(parents=True, exist_ok=True)
    
    def export_unlabeled_articles(
        self,
        db_path: str = "news_sources.db",
        limit: Optional[int] = None,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
    ) -> pd.DataFrame:
        """
        Export articles from database for labeling.
        
        Prioritizes articles with:
        - Low ML confidence (uncertain predictions)
        - Diverse sources
        - Recent articles
        """
        logger.info("Exporting articles from database...")
        
        # Since we don't have a separate articles table, we'll simulate this
        # In production, you'd query from a proper articles table
        
        # For now, create a template for the labeling format
        df = pd.DataFrame(columns=[
            "article_id",
            "title",
            "summary",
            "content",
            "source_name",
            "source_bias",
            "ml_prediction",
            "ml_confidence",
            "published",
            "url",
        ])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.labeling_dir / f"unlabeled_articles_{timestamp}.csv"
        df.to_csv(output_path, index=False)
        
        logger.info(f"Exported {len(df)} articles to {output_path}")
        return df
    
    def import_labeled_data(
        self,
        labeled_file: str,
        label_column: str = "human_label",
    ) -> pd.DataFrame:
        """
        Import labeled data and validate labels.
        
        Expected columns:
        - article_id
        - title, summary, content
        - human_label (one of: Left-Leaning, Center-Left, Centrist, Center-Right, Right-Leaning)
        - annotator_id (optional, for inter-annotator agreement)
        - confidence (optional, annotator confidence)
        """
        logger.info(f"Importing labeled data from {labeled_file}...")
        
        df = pd.read_csv(labeled_file)
        
        # Validate required columns
        required_cols = ["article_id", "title", label_column]
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Validate labels
        valid_labels = {
            "Left-Leaning",
            "Center-Left",
            "Centrist",
            "Center-Right",
            "Right-Leaning",
        }
        invalid_labels = set(df[label_column].unique()) - valid_labels
        if invalid_labels:
            logger.warning(f"Found invalid labels: {invalid_labels}")
            df = df[df[label_column].isin(valid_labels)]
        
        logger.info(f"Imported {len(df)} labeled articles")
        logger.info(f"Label distribution:\n{df[label_column].value_counts()}")
        
        return df
    
    def create_training_dataset(
        self,
        labeled_files: List[str],
        stratify: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create train/val/test splits from labeled data.
        
        Returns:
            train_df, val_df, test_df
        """
        logger.info("Creating training dataset...")
        
        # Combine all labeled files
        dfs = []
        for file in labeled_files:
            df = self.import_labeled_data(file)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(subset=["article_id"])
        logger.info(f"Total unique labeled articles: {len(combined_df)}")
        
        # Create splits
        train_size = self.config["data"]["train_split"]
        val_size = self.config["data"]["val_split"]
        test_size = self.config["data"]["test_split"]
        
        # First split: train+val vs test
        stratify_col = combined_df["human_label"] if stratify else None
        train_val_df, test_df = train_test_split(
            combined_df,
            test_size=test_size,
            stratify=stratify_col,
            random_state=42,
        )
        
        # Second split: train vs val
        val_ratio = val_size / (train_size + val_size)
        stratify_col = train_val_df["human_label"] if stratify else None
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_ratio,
            stratify=stratify_col,
            random_state=42,
        )
        
        logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        # Save splits
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        train_df.to_csv(self.processed_dir / f"train_{timestamp}.csv", index=False)
        val_df.to_csv(self.processed_dir / f"val_{timestamp}.csv", index=False)
        test_df.to_csv(self.processed_dir / f"test_{timestamp}.csv", index=False)
        
        return train_df, val_df, test_df
    
    def augment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data augmentation techniques.
        
        Techniques:
        - Synonym replacement
        - Random word swap
        - Back-translation (if enabled)
        """
        if not self.config["training"]["augmentation"]["enabled"]:
            return df
        
        logger.info("Applying data augmentation...")
        # TODO: Implement augmentation techniques
        # This is a placeholder for now
        return df
    
    def compute_inter_annotator_agreement(
        self,
        labeled_file: str,
    ) -> Dict[str, float]:
        """
        Compute inter-annotator agreement metrics.
        
        Requires multiple annotators per article.
        Returns Cohen's Kappa, Fleiss' Kappa, etc.
        """
        logger.info("Computing inter-annotator agreement...")
        # TODO: Implement IAA metrics
        return {"cohen_kappa": 0.0, "fleiss_kappa": 0.0}
    
    def export_for_active_learning(
        self,
        model_predictions: pd.DataFrame,
        strategy: str = "uncertainty_sampling",
        n_samples: int = 100,
    ) -> pd.DataFrame:
        """
        Select samples for labeling using active learning.
        
        Strategies:
        - uncertainty_sampling: Select samples with lowest confidence
        - diversity_sampling: Select diverse samples
        - committee_disagreement: Select samples with high model disagreement
        """
        logger.info(f"Selecting {n_samples} samples using {strategy}...")
        
        if strategy == "uncertainty_sampling":
            # Select samples with lowest confidence
            sorted_df = model_predictions.sort_values("ml_confidence")
            selected = sorted_df.head(n_samples)
        else:
            # Random sampling as fallback
            selected = model_predictions.sample(n=min(n_samples, len(model_predictions)))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.labeling_dir / f"active_learning_{timestamp}.csv"
        selected.to_csv(output_path, index=False)
        
        logger.info(f"Exported {len(selected)} articles for labeling")
        return selected


def main():
    """Example usage."""
    collector = DataCollector()
    
    # Step 1: Export unlabeled articles for initial labeling
    unlabeled = collector.export_unlabeled_articles(limit=1000)
    print(f"Exported {len(unlabeled)} unlabeled articles")
    
    # Step 2: After labeling, import and create training dataset
    # labeled_files = ["data/labeling/labeled_batch_1.csv"]
    # train_df, val_df, test_df = collector.create_training_dataset(labeled_files)
    # print(f"Created training dataset: {len(train_df)} train, {len(val_df)} val, {len(test_df)} test")


if __name__ == "__main__":
    main()
