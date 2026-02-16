"""
Integration script to update bias classifier with your newly trained model.

This will replace the default politicalBiasBERT model with your custom trained model
which has been trained on 17,000+ articles and should give much better accuracy.

Run this after you've extracted the model to models/custom_bias_detector/
"""

import os
from pathlib import Path

def check_model_exists():
    """Check if the custom model has been extracted."""
    model_path = Path("models/custom_bias_detector")
    
    required_files = [
        "config.json",
        "pytorch_model.bin",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt"
    ]
    
    if not model_path.exists():
        print("❌ Model directory not found: models/custom_bias_detector")
        print("\nPlease:")
        print("1. Download political_bias_detector_model.zip from Google Colab")
        print("2. Run: bash setup_trained_model.sh")
        return False
    
    missing_files = [f for f in required_files if not (model_path / f).exists()]
    
    if missing_files:
        print(f"❌ Missing model files: {', '.join(missing_files)}")
        return False
    
    print(f"✅ Model found at {model_path}")
    return True

def update_bias_classifier():
    """Update the bias classifier to use the custom model."""
    
    if not check_model_exists():
        return
    
    classifier_path = Path("src/backend/bias_classifier.py")
    
    if not classifier_path.exists():
        print(f"❌ bias_classifier.py not found at {classifier_path}")
        return
    
    print(f"\n📝 Reading {classifier_path}...")
    content = classifier_path.read_text()
    
    # Check if already using custom model
    if "models/custom_bias_detector" in content:
        print("✅ Already using custom model!")
        return
    
    # Replace the default model ID
    old_line = '    direction_model_id: str = "bucketresearch/politicalBiasBERT"'
    new_line = '    direction_model_id: str = "models/custom_bias_detector"'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        classifier_path.write_text(content)
        print("✅ Updated bias_classifier.py!")
        print("\n📊 Changes made:")
        print(f"  Old: {old_line}")
        print(f"  New: {new_line}")
        print("\n✅ Your custom trained model is now active!")
        print("\nNext steps:")
        print("1. Restart the Streamlit app if it's running")
        print("2. Test the classifier on some articles")
        print("3. Compare the new results - should be much more accurate!")
    else:
        print("❌ Could not find the line to replace")
        print("Manual update needed in src/backend/bias_classifier.py")

if __name__ == "__main__":
    print("="*70)
    print("Custom Model Integration Script")
    print("="*70)
    print()
    update_bias_classifier()
