"""
RunPod Training Script - Optimized for Speed

This script is optimized for RunPod's high-performance GPUs.
Expected training time: 3-5 minutes on RTX 4090, 2-3 minutes on A100.

Usage on RunPod:
1. Deploy a PyTorch pod with RTX 4090 or A100
2. Open Jupyter Lab
3. Upload this script
4. Run: python runpod_train.py
5. Download the model
6. STOP THE POD!
"""

import os
import sys
import time
from pathlib import Path

def install_packages():
    """Install required packages."""
    print("📦 Installing packages...")
    os.system("pip install -q transformers datasets accelerate scikit-learn kagglehub")
    print("✅ Packages installed\n")

def download_and_prepare_data():
    """Download dataset and prepare for training."""
    import kagglehub
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    print("📥 Downloading Kaggle dataset...")
    dataset_path = kagglehub.dataset_download("cl0ud0/news-political-bias-classification-dataset")
    
    # Load dataset
    csv_files = list(Path(dataset_path).glob("*.csv"))
    df = pd.read_csv(csv_files[0])
    print(f"✅ Loaded {len(df)} samples\n")
    
    # Normalize labels
    LABEL_MAP = {
        "left": "Left-Leaning",
        "left-leaning": "Left-Leaning",
        "center": "Centrist",
        "centrist": "Centrist",
        "right": "Right-Leaning",
        "right-leaning": "Right-Leaning",
    }
    
    df['label_normalized'] = df['label'].str.lower().map(LABEL_MAP)
    df = df[df['label_normalized'].notna()]
    
    label_to_id = {
        "Left-Leaning": 0,
        "Centrist": 1,
        "Right-Leaning": 2,
    }
    df['label_id'] = df['label_normalized'].map(label_to_id)
    
    # Split data
    train_val_df, test_df = train_test_split(
        df, test_size=0.1, stratify=df['label_id'], random_state=42
    )
    train_df, val_df = train_test_split(
        train_val_df, test_size=0.1, stratify=train_val_df['label_id'], random_state=42
    )
    
    print(f"📊 Data splits:")
    print(f"   Train: {len(train_df)}")
    print(f"   Val:   {len(val_df)}")
    print(f"   Test:  {len(test_df)}\n")
    
    return train_df, val_df, test_df

def train_model_fast(train_df, val_df, test_df):
    """Train model with optimized settings for speed."""
    from datasets import Dataset
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
    )
    from sklearn.metrics import accuracy_score, f1_score, classification_report
    import torch
    
    # Check GPU
    if torch.cuda.is_available():
        print(f"🚀 GPU Available: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB\n")
    else:
        print("⚠️  No GPU found! Training will be slow.\n")
    
    # Prepare datasets
    print("📚 Preparing datasets...")
    train_dataset = Dataset.from_dict({
        'text': train_df['text'].tolist(),
        'label': train_df['label_id'].tolist()
    })
    val_dataset = Dataset.from_dict({
        'text': val_df['text'].tolist(),
        'label': val_df['label_id'].tolist()
    })
    test_dataset = Dataset.from_dict({
        'text': test_df['text'].tolist(),
        'label': test_df['label_id'].tolist()
    })
    
    # Load model - using smaller model for speed
    MODEL_NAME = "distilroberta-base"
    print(f"🤖 Loading model: {MODEL_NAME}...")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=3,
        id2label={0: "Left-Leaning", 1: "Centrist", 2: "Right-Leaning"},
        label2id={"Left-Leaning": 0, "Centrist": 1, "Right-Leaning": 2}
    )
    
    # Tokenize with optimized batch size
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=512
        )
    
    print("🔤 Tokenizing datasets...")
    train_dataset = train_dataset.map(tokenize_function, batched=True, batch_size=1000)
    val_dataset = val_dataset.map(tokenize_function, batched=True, batch_size=1000)
    test_dataset = test_dataset.map(tokenize_function, batched=True, batch_size=1000)
    
    # Compute metrics
    def compute_metrics(pred):
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        return {
            'accuracy': accuracy_score(labels, preds),
            'f1': f1_score(labels, preds, average='weighted')
        }
    
    # Training arguments optimized for speed
    print("⚙️  Configuring training...\n")
    
    # Adjust batch size based on GPU memory
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        if gpu_memory > 40:  # A100
            batch_size = 32
        elif gpu_memory > 20:  # RTX 4090, V100
            batch_size = 24
        else:
            batch_size = 16
    else:
        batch_size = 8
    
    training_args = TrainingArguments(
        output_dir="./bias_detector_model",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,  # Slightly higher for faster convergence
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=3,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=50,
        save_total_limit=1,  # Save space
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=4,  # Parallel data loading
        gradient_accumulation_steps=1,
        optim="adamw_torch_fused" if torch.cuda.is_available() else "adamw_torch",
        report_to="none",
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print(f"🚀 Starting training with batch size {batch_size}...\n")
    start_time = time.time()
    
    trainer.train()
    
    training_time = time.time() - start_time
    print(f"\n✅ Training completed in {training_time/60:.1f} minutes!\n")
    
    # Evaluate
    print("📊 Evaluating on test set...")
    test_results = trainer.evaluate(test_dataset)
    print(f"\nTest Results: {test_results}\n")
    
    # Classification report
    predictions = trainer.predict(test_dataset)
    preds = predictions.predictions.argmax(-1)
    labels = predictions.label_ids
    
    print("📋 Classification Report:")
    print(classification_report(
        labels, preds,
        target_names=['Left-Leaning', 'Centrist', 'Right-Leaning'],
        zero_division=0
    ))
    
    # Save model
    output_dir = "./political_bias_detector_final"
    print(f"\n💾 Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Create zip
    import shutil
    print("📦 Creating download package...")
    shutil.make_archive('political_bias_detector_model', 'zip', output_dir)
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"⏱️  Total time: {training_time/60:.1f} minutes")
    print(f"📦 Download: political_bias_detector_model.zip")
    print(f"📊 Test Accuracy: {test_results['eval_accuracy']:.2%}")
    print(f"📊 Test F1 Score: {test_results['eval_f1']:.2%}")
    print("\n⚠️  IMPORTANT: Stop your RunPod instance now to avoid charges!")
    print("="*70)

def main():
    """Main execution."""
    print("="*70)
    print("RunPod Fast Training - Political Bias Detector")
    print("="*70)
    print()
    
    # Install packages
    install_packages()
    
    # Download and prepare data
    train_df, val_df, test_df = download_and_prepare_data()
    
    # Train model
    train_model_fast(train_df, val_df, test_df)

if __name__ == "__main__":
    main()
