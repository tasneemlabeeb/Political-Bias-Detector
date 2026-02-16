# Political Bias Detector - Model Training Guide

## Overview

This directory contains the infrastructure for training and fine-tuning political bias classification models using MLflow for experiment tracking.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r training/requirements-training.txt
```

### 2. Setup MLflow

```bash
python training/mlflow_setup.py
```

This creates:
- MLflow tracking directory (`mlruns/`)
- Experiment folders
- Initial configuration

### 3. Prepare Training Data

```bash
python training/data_collection.py
```

**Data Format:**
Your labeled CSV should have these columns:
- `article_id`: Unique identifier
- `title`: Article title
- `summary`: Article summary (optional)
- `content`: Full article text (optional)
- `human_label`: One of `Left-Leaning`, `Center-Left`, `Centrist`, `Center-Right`, `Right-Leaning`
- `source_name`: News source (optional, for analysis)

### 4. Train a Model

```python
from training.train_model import BiasModelTrainer

trainer = BiasModelTrainer()
trainer.train(
    train_file="data/processed/train_20260216_120000.csv",
    val_file="data/processed/val_20260216_120000.csv",
    output_dir="models/custom_roberta"
)
```

### 5. View MLflow UI

```bash
mlflow ui --backend-store-uri mlruns
```

Open http://localhost:5000 to view experiments, metrics, and models.

## Directory Structure

```
training/
├── config.yaml                 # Training configuration
├── data_collection.py          # Data preparation pipeline
├── train_model.py              # Model training with MLflow
├── evaluate_model.py           # Evaluation and analysis
├── mlflow_setup.py            # MLflow initialization
├── requirements-training.txt   # Training dependencies
└── README.md                   # This file

data/
├── raw/                        # Original data
├── processed/                  # Train/val/test splits
└── labeling/                   # Data for human labeling

models/                         # Saved model checkpoints
mlruns/                        # MLflow tracking data
logs/                          # Training logs
evaluation_results/            # Evaluation outputs
```

## Training Pipeline

### Step 1: Data Collection

Collect articles from your database and export for labeling:

```python
from training.data_collection import DataCollector

collector = DataCollector()

# Export unlabeled articles
unlabeled = collector.export_unlabeled_articles(limit=1000)

# After labeling, import and create splits
train_df, val_df, test_df = collector.create_training_dataset([
    "data/labeling/labeled_batch_1.csv",
    "data/labeling/labeled_batch_2.csv",
])
```

### Step 2: Model Training

Train with different base models:

```python
from training.train_model import BiasModelTrainer

trainer = BiasModelTrainer()

# Option 1: RoBERTa (recommended)
trainer.train(
    train_file="data/processed/train_20260216_120000.csv",
    val_file="data/processed/val_20260216_120000.csv",
    model_name="roberta-base",
    output_dir="models/roberta_v1"
)

# Option 2: BERT
trainer.train(
    train_file="data/processed/train_20260216_120000.csv",
    val_file="data/processed/val_20260216_120000.csv",
    model_name="bert-base-uncased",
    output_dir="models/bert_v1"
)

# Option 3: DistilBERT (faster, smaller)
trainer.train(
    train_file="data/processed/train_20260216_120000.csv",
    val_file="data/processed/val_20260216_120000.csv",
    model_name="distilbert-base-uncased",
    output_dir="models/distilbert_v1"
)
```

### Step 3: Evaluation

```python
from training.evaluate_model import ModelEvaluator

evaluator = ModelEvaluator(output_dir="evaluation_results")

# Evaluate on test set
# First, load test data and make predictions
# Then evaluate:
results = evaluator.evaluate(
    y_true=test_labels,
    y_pred=predictions,
    y_proba=probabilities,
    metadata=test_metadata
)
```

### Step 4: Model Registration

```python
from training.mlflow_setup import MLflowManager

manager = MLflowManager()

# Register best model
manager.register_model(
    model_uri="runs:/YOUR_RUN_ID/model",
    model_name="political_bias_classifier",
    description="RoBERTa fine-tuned on 10k labeled articles"
)

# Promote to production
manager.promote_model_to_production(
    model_name="political_bias_classifier",
    version=1
)
```

## Configuration

Edit `training/config.yaml` to customize:

### Model Configuration
```yaml
model:
  custom:
    architecture: "roberta-base"
    learning_rate: 3e-5
    dropout: 0.1
```

### Training Configuration
```yaml
training:
  epochs: 5
  batch_size: 16
  early_stopping_patience: 3
  fp16: true  # Enable for GPU
```

### Data Configuration
```yaml
data:
  train_split: 0.8
  val_split: 0.1
  test_split: 0.1
  max_text_length: 5000
```

## Active Learning Workflow

Iteratively improve your model with active learning:

```python
from training.data_collection import DataCollector

collector = DataCollector()

# 1. Get model predictions on unlabeled data
unlabeled_df = collector.export_unlabeled_articles()

# 2. Run predictions (using your trained model)
# predictions_df = model.predict(unlabeled_df)

# 3. Select uncertain samples for labeling
selected = collector.export_for_active_learning(
    predictions_df,
    strategy="uncertainty_sampling",
    n_samples=100
)

# 4. Label selected samples
# ... manual labeling ...

# 5. Add to training set and retrain
```

## Best Practices

### 1. **Data Quality**
- Aim for at least 1000+ labeled examples per class
- Balance classes (or use class weighting)
- Use 3+ annotators for quality labels
- Track inter-annotator agreement (Cohen's Kappa)

### 2. **Model Selection**
- Start with RoBERTa-base (best accuracy)
- Use DistilBERT for faster inference
- Consider domain-specific pre-training

### 3. **Training**
- Use early stopping to prevent overfitting
- Monitor validation metrics, not just training loss
- Experiment with learning rates (1e-5 to 5e-5)
- Enable mixed precision (fp16) for GPU training

### 4. **Evaluation**
- Always evaluate on held-out test set
- Check calibration (confidence vs accuracy)
- Analyze errors by source
- Monitor fairness across different news outlets

### 5. **Versioning**
- Track all experiments in MLflow
- Tag experiments with meaningful descriptions
- Save training data alongside models
- Document model limitations

## Hardware Requirements

### CPU Training
- 16GB+ RAM
- Training time: ~2-4 hours for 5 epochs on 10k articles

### GPU Training (Recommended)
- NVIDIA GPU with 8GB+ VRAM (RTX 3060+)
- CUDA 11.8+
- Training time: ~20-40 minutes for 5 epochs on 10k articles

### Apple Silicon (M1/M2/M3)
- MPS acceleration supported
- 16GB+ unified memory recommended
- Training time: ~1-2 hours for 5 epochs on 10k articles

## Troubleshooting

### Out of Memory
```yaml
# Reduce batch size
training:
  batch_size: 8
  gradient_accumulation_steps: 4  # Effective batch size = 8*4 = 32
```

### Slow Training
```yaml
# Enable mixed precision (GPU only)
training:
  fp16: true

# Use smaller model
model:
  custom:
    architecture: "distilbert-base-uncased"
```

### Poor Performance
- Check data quality and balance
- Increase training data
- Adjust learning rate
- Try different base models
- Check for label noise

## Next Steps

1. **Data Labeling**: Set up a labeling interface (Label Studio, Prodigy)
2. **Model Serving**: Deploy models via FastAPI (see backend documentation)
3. **Monitoring**: Track model performance in production
4. **Continuous Training**: Set up automated retraining pipelines

## Resources

- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Fine-tuning Guide](https://huggingface.co/docs/transformers/training)
- [Model Evaluation Best Practices](https://scikit-learn.org/stable/modules/model_evaluation.html)
