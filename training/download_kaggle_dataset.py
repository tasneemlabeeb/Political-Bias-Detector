#!/usr/bin/env python3
"""
Download and integrate Kaggle political bias dataset.

This script:
1. Downloads the Kaggle political bias classification dataset
2. Processes and normalizes the data
3. Merges with locally collected articles
4. Creates enhanced training/validation/test splits
"""

import os
import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

# Add project root to path
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Label mapping to ensure consistency
BIAS_LABEL_MAP = {
    "Left-Leaning": 0,
    "Center-Left": 1,
    "Centrist": 2,
    "Center-Right": 3,
    "Right-Leaning": 4,
}

# Alternative label names that might appear in datasets
LABEL_ALIASES = {
    "left": "Left-Leaning",
    "left-leaning": "Left-Leaning",
    "liberal": "Left-Leaning",
    "center-left": "Center-Left",
    "left-center": "Center-Left",
    "center": "Centrist",
    "centrist": "Centrist",
    "neutral": "Centrist",
    "center-right": "Center-Right",
    "right-center": "Center-Right",
    "right": "Right-Leaning",
    "right-leaning": "Right-Leaning",
    "conservative": "Right-Leaning",
}


def download_kaggle_dataset():
    """Download the Kaggle political bias dataset."""
    logger.info("Downloading Kaggle dataset...")
    
    try:
        import kagglehub
        
        # Download latest version
        path = kagglehub.dataset_download("cl0ud0/news-political-bias-classification-dataset")
        
        logger.info(f"✅ Dataset downloaded to: {path}")
        return path
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        logger.info("\n💡 Troubleshooting:")
        logger.info("   1. Authenticate with Kaggle: https://github.com/Kaggle/kagglehub#authenticate")
        logger.info("   2. Set KAGGLE_USERNAME and KAGGLE_KEY environment variables")
        logger.info("   3. Or place kaggle.json in ~/.kaggle/")
        return None


def normalize_label(label_value):
    """Normalize various label formats to standard names."""
    if pd.isna(label_value):
        return None
    
    label_str = str(label_value).strip().lower()
    
    # Check aliases
    if label_str in LABEL_ALIASES:
        return LABEL_ALIASES[label_str]
    
    # Check if already in standard format
    for standard_label in BIAS_LABEL_MAP.keys():
        if label_str == standard_label.lower():
            return standard_label
    
    return None


def process_kaggle_dataset(dataset_path):
    """
    Process the Kaggle dataset and normalize it.
    
    The dataset should have columns like:
    - text/article/content
    - label/bias/political_bias
    """
    logger.info(f"Processing Kaggle dataset from: {dataset_path}")
    
    # Find CSV files in the dataset directory
    dataset_dir = Path(dataset_path)
    csv_files = list(dataset_dir.glob("*.csv"))
    
    if not csv_files:
        logger.error("No CSV files found in dataset directory!")
        return None
    
    logger.info(f"Found {len(csv_files)} CSV file(s)")
    
    all_data = []
    
    for csv_file in csv_files:
        logger.info(f"Reading: {csv_file.name}")
        df = pd.read_csv(csv_file)
        
        logger.info(f"  Columns: {list(df.columns)}")
        logger.info(f"  Rows: {len(df)}")
        
        # Identify text column
        text_col = None
        for col in ['text', 'article', 'content', 'full_text', 'body']:
            if col in df.columns:
                text_col = col
                break
        
        # Identify label column
        label_col = None
        for col in ['label', 'bias', 'political_bias', 'category', 'class']:
            if col in df.columns:
                label_col = col
                break
        
        if not text_col or not label_col:
            logger.warning(f"  ⚠️  Could not identify text or label columns, skipping")
            continue
        
        # Extract and normalize
        for _, row in df.iterrows():
            text = str(row[text_col]).strip()
            label_raw = row[label_col]
            
            # Normalize label
            label = normalize_label(label_raw)
            
            if not label or label not in BIAS_LABEL_MAP:
                continue
            
            if len(text) < 50:  # Skip very short texts
                continue
            
            all_data.append({
                'text': text,
                'label': label,
                'label_id': BIAS_LABEL_MAP[label],
                'source': 'kaggle_dataset',
                'title': text[:100] + '...' if len(text) > 100 else text,
            })
    
    if not all_data:
        logger.error("No valid data extracted from Kaggle dataset!")
        return None
    
    kaggle_df = pd.DataFrame(all_data)
    
    logger.info(f"\n✅ Processed {len(kaggle_df)} samples from Kaggle dataset")
    logger.info("\nLabel Distribution:")
    logger.info(kaggle_df['label'].value_counts().to_string())
    
    return kaggle_df


def merge_datasets(kaggle_df, local_csv_path=None):
    """Merge Kaggle dataset with locally collected articles."""
    logger.info("\nMerging datasets...")
    
    datasets = [kaggle_df]
    
    # Find local dataset if not provided
    if local_csv_path is None:
        data_dir = Path("data/raw")
        csv_files = sorted(data_dir.glob("training_dataset_*.csv"))
        if csv_files:
            local_csv_path = csv_files[-1]  # Get most recent
    
    # Load local dataset if exists
    if local_csv_path and Path(local_csv_path).exists():
        logger.info(f"Loading local dataset: {local_csv_path}")
        local_df = pd.read_csv(local_csv_path)
        
        # Ensure consistent columns
        if 'text' not in local_df.columns and 'summary' in local_df.columns:
            local_df['text'] = local_df['summary']
        
        # Select common columns
        common_cols = ['text', 'label', 'label_id', 'source', 'title']
        local_df = local_df[[col for col in common_cols if col in local_df.columns]]
        
        logger.info(f"  Local dataset: {len(local_df)} samples")
        datasets.append(local_df)
    
    # Combine
    merged_df = pd.concat(datasets, ignore_index=True)
    
    # Remove duplicates based on text
    original_len = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['text'], keep='first')
    duplicates_removed = original_len - len(merged_df)
    
    if duplicates_removed > 0:
        logger.info(f"  Removed {duplicates_removed} duplicate samples")
    
    logger.info(f"\n✅ Merged dataset: {len(merged_df)} total samples")
    logger.info("\nFinal Label Distribution:")
    logger.info(merged_df['label'].value_counts().to_string())
    
    return merged_df


def create_balanced_splits(df, train_ratio=0.8, val_ratio=0.1):
    """Create balanced train/val/test splits with stratification."""
    from sklearn.model_selection import train_test_split
    
    logger.info("\nCreating balanced train/val/test splits...")
    
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
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    train_path = output_dir / f"train_enhanced_{timestamp}.csv"
    val_path = output_dir / f"val_enhanced_{timestamp}.csv"
    test_path = output_dir / f"test_enhanced_{timestamp}.csv"
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"\n✅ Dataset splits saved:")
    logger.info(f"   Train: {len(train_df)} samples → {train_path}")
    logger.info(f"   Val:   {len(val_df)} samples → {val_path}")
    logger.info(f"   Test:  {len(test_df)} samples → {test_path}")
    
    # Show distribution per split
    logger.info("\nTrain set distribution:")
    logger.info(train_df['label'].value_counts().to_string())
    
    return train_path, val_path, test_path


def main():
    """Main execution."""
    print("="*70)
    print("Political Bias Detector - Kaggle Dataset Integration")
    print("="*70)
    print()
    
    # Step 1: Download Kaggle dataset
    print("📥 Step 1: Downloading Kaggle dataset...")
    dataset_path = download_kaggle_dataset()
    
    if not dataset_path:
        print("\n❌ Failed to download Kaggle dataset!")
        print("\n💡 You can manually download from:")
        print("   https://www.kaggle.com/datasets/cl0ud0/news-political-bias-classification-dataset")
        print("   Then update the path in this script.")
        return
    
    # Step 2: Process Kaggle dataset
    print("\n📊 Step 2: Processing Kaggle dataset...")
    kaggle_df = process_kaggle_dataset(dataset_path)
    
    if kaggle_df is None or kaggle_df.empty:
        print("\n❌ Failed to process Kaggle dataset!")
        return
    
    # Step 3: Merge with local data
    print("\n🔄 Step 3: Merging with local dataset...")
    merged_df = merge_datasets(kaggle_df)
    
    # Step 4: Create balanced splits
    print("\n✂️  Step 4: Creating balanced train/val/test splits...")
    train_path, val_path, test_path = create_balanced_splits(merged_df)
    
    print("\n" + "="*70)
    print("✅ Dataset preparation complete!")
    print("\n📈 Dataset Summary:")
    print(f"   Total samples: {len(merged_df)}")
    print(f"   Unique sources: {merged_df['source'].nunique()}")
    print(f"   Classes: {len(merged_df['label'].unique())}")
    
    print("\n🚀 Next step:")
    print("   Run model training: python training/train_model.py")
    print("   Or use the training paths above in your training script")
    print("="*70)


if __name__ == "__main__":
    main()
