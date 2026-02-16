#!/usr/bin/env python3
"""
Collect and prepare training data from multiple sources.

This script helps you build a labeled dataset for political bias detection by:
1. Collecting articles from your database
2. Using source-assigned bias as ground truth labels
3. Creating a properly formatted training dataset
4. Optionally downloading public datasets
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import logging

# Add project root to path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

from src.backend.source_manager import SourceManager
from src.backend.news_crawler import NewsCrawler

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


BIAS_LABEL_MAP = {
    "Left-Leaning": 0,
    "Center-Left": 1,
    "Centrist": 2,
    "Center-Right": 3,
    "Right-Leaning": 4,
}


def collect_articles_from_database(db_path: str = "news_sources.db", min_articles: int = 50) -> pd.DataFrame:
    """Collect articles that have been fetched and stored."""
    logger.info("Collecting articles from current crawl session...")
    
    # Since articles are stored in session state, we'll use the crawler
    # to fetch fresh articles and use source bias as labels
    sm = SourceManager(db_path)
    crawler = NewsCrawler(sm, max_articles_per_source=min_articles)
    
    logger.info("Crawling sources to collect training data...")
    articles_df = crawler.crawl_all_sources()
    
    if articles_df.empty:
        logger.warning("No articles found! Please run 'Fetch Latest News' in the app first.")
        return pd.DataFrame()
    
    logger.info(f"Collected {len(articles_df)} articles from {articles_df['source_name'].nunique()} sources")
    
    return articles_df


def prepare_training_dataset(articles_df: pd.DataFrame, output_dir: str = "data/raw") -> str:
    """
    Prepare articles for training.
    
    Uses source-assigned bias as ground truth labels.
    """
    if articles_df.empty:
        logger.error("No articles to prepare!")
        return None
    
    # Create training dataframe
    training_data = []
    
    for _, row in articles_df.iterrows():
        # Combine title and summary/content for full text
        title = str(row.get('title', '')).strip()
        summary = str(row.get('summary', '')).strip()
        content = str(row.get('content', '')).strip()
        
        # Use the longer text between summary and content
        body = summary if len(summary) > len(content) else content
        full_text = f"{title}. {body}" if body else title
        
        # Skip if text is too short
        if len(full_text) < 50:
            continue
        
        # Get bias label from source
        bias_label = row.get('political_bias', 'Unclassified')
        
        # Skip unclassified
        if bias_label == 'Unclassified' or bias_label not in BIAS_LABEL_MAP:
            continue
        
        training_data.append({
            'text': full_text,
            'title': title,
            'summary': body,
            'label': bias_label,
            'label_id': BIAS_LABEL_MAP[bias_label],
            'source': row.get('source_name', ''),
            'url': row.get('link', ''),
            'published': row.get('published', ''),
        })
    
    if not training_data:
        logger.error("No valid training samples after filtering!")
        return None
    
    training_df = pd.DataFrame(training_data)
    
    # Show distribution
    logger.info("\nLabel Distribution:")
    logger.info(training_df['label'].value_counts().to_string())
    
    # Check class balance
    min_samples = training_df['label'].value_counts().min()
    max_samples = training_df['label'].value_counts().max()
    imbalance_ratio = max_samples / min_samples if min_samples > 0 else float('inf')
    
    if imbalance_ratio > 3:
        logger.warning(f"⚠️  Dataset is imbalanced (ratio: {imbalance_ratio:.1f}x)")
        logger.warning("   Consider collecting more articles from underrepresented sources")
    
    # Save dataset
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"training_dataset_{timestamp}.csv")
    training_df.to_csv(output_path, index=False)
    
    logger.info(f"\n✅ Saved {len(training_df)} training samples to: {output_path}")
    logger.info(f"   Total unique sources: {training_df['source'].nunique()}")
    
    return output_path


def split_dataset(dataset_path: str, train_ratio: float = 0.8, val_ratio: float = 0.1):
    """Split dataset into train/val/test sets with stratification."""
    from sklearn.model_selection import train_test_split
    
    logger.info(f"\nSplitting dataset: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # First split: train+val vs test
    test_ratio = 1.0 - train_ratio - val_ratio
    train_val_df, test_df = train_test_split(
        df, 
        test_size=test_ratio, 
        stratify=df['label'],
        random_state=42
    )
    
    # Second split: train vs val
    val_size_adjusted = val_ratio / (train_ratio + val_ratio)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=val_size_adjusted,
        stratify=train_val_df['label'],
        random_state=42
    )
    
    # Save splits
    output_dir = os.path.dirname(dataset_path)
    processed_dir = output_dir.replace('raw', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    train_path = os.path.join(processed_dir, f"train_{timestamp}.csv")
    val_path = os.path.join(processed_dir, f"val_{timestamp}.csv")
    test_path = os.path.join(processed_dir, f"test_{timestamp}.csv")
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"\n✅ Dataset split complete:")
    logger.info(f"   Train: {len(train_df)} samples → {train_path}")
    logger.info(f"   Val:   {len(val_df)} samples → {val_path}")
    logger.info(f"   Test:  {len(test_df)} samples → {test_path}")
    
    return train_path, val_path, test_path


def download_public_datasets(output_dir: str = "data/raw"):
    """
    Download public political bias datasets.
    
    Note: This is a placeholder. You can add real dataset downloads here.
    Potential sources:
    - AllSides Media Bias Ratings
    - Media Bias Fact Check (MBFC)
    - Hyperpartisan News Detection datasets
    """
    logger.info("\n📦 Public Dataset Sources:")
    logger.info("   1. AllSides Media Bias Ratings: https://www.allsides.com/media-bias")
    logger.info("   2. MBFC: https://mediabiasfactcheck.com/")
    logger.info("   3. Kaggle Political Bias datasets")
    logger.info("\n   Manual download recommended for these sources.")
    logger.info("   Save CSV files to: data/raw/")


def main():
    """Main execution."""
    print("="*70)
    print("Political Bias Detector - Training Data Collection")
    print("="*70)
    print()
    
    # Step 1: Collect articles from current sources
    print("📊 Step 1: Collecting articles from news sources...")
    articles_df = collect_articles_from_database()
    
    if articles_df.empty:
        print("\n❌ No articles found!")
        print("\n💡 Next steps:")
        print("   1. Open the Streamlit app")
        print("   2. Click 'Fetch Latest News' to crawl sources")
        print("   3. Run this script again")
        print("\n   Or add more news sources with different biases.")
        return
    
    # Step 2: Prepare training dataset
    print("\n📝 Step 2: Preparing training dataset...")
    dataset_path = prepare_training_dataset(articles_df)
    
    if not dataset_path:
        print("\n❌ Failed to create training dataset!")
        return
    
    # Step 3: Split into train/val/test
    print("\n✂️  Step 3: Splitting dataset...")
    train_path, val_path, test_path = split_dataset(dataset_path)
    
    # Step 4: Information about public datasets
    print("\n" + "="*70)
    download_public_datasets()
    
    print("\n" + "="*70)
    print("✅ Data collection complete!")
    print("\n🚀 Next steps:")
    print("   1. Review the generated datasets in data/processed/")
    print("   2. (Optional) Add more labeled data from public sources")
    print("   3. Run training: python training/train_model.py")
    print("="*70)


if __name__ == "__main__":
    main()
