"""
Model Evaluation and Analysis Tools

This module provides:
- Comprehensive model evaluation metrics
- Error analysis
- Bias fairness analysis
- Calibration analysis
- Performance visualization
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
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


class ModelEvaluator:
    """Comprehensive model evaluation and analysis."""
    
    def __init__(self, output_dir: str = "evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        metadata: Optional[pd.DataFrame] = None,
    ) -> Dict:
        """
        Comprehensive model evaluation.
        
        Args:
            y_true: Ground truth labels (numeric)
            y_pred: Predicted labels (numeric)
            y_proba: Prediction probabilities (optional)
            metadata: Additional metadata (source, date, etc.)
        
        Returns:
            Dictionary with all evaluation metrics
        """
        logger.info("Running comprehensive evaluation...")
        
        results = {}
        
        # Basic metrics
        results["accuracy"] = accuracy_score(y_true, y_pred)
        results["cohen_kappa"] = cohen_kappa_score(y_true, y_pred)
        
        # Per-class metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, average=None, labels=range(5)
        )
        
        results["per_class_metrics"] = {
            LABEL_NAMES[i]: {
                "precision": precision[i],
                "recall": recall[i],
                "f1": f1[i],
                "support": int(support[i]),
            }
            for i in range(5)
        }
        
        # Macro/weighted averages
        results["f1_macro"] = f1_score(y_true, y_pred, average="macro")
        results["f1_weighted"] = f1_score(y_true, y_pred, average="weighted")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=range(5))
        results["confusion_matrix"] = cm.tolist()
        
        # Generate visualizations
        self.plot_confusion_matrix(cm, "confusion_matrix.png")
        
        if y_proba is not None:
            # Calibration analysis
            calibration_results = self.analyze_calibration(y_true, y_proba)
            results["calibration"] = calibration_results
            
            # Confidence analysis
            confidence_results = self.analyze_confidence(y_true, y_pred, y_proba)
            results["confidence"] = confidence_results
        
        if metadata is not None:
            # Error analysis by source
            error_analysis = self.analyze_errors_by_source(
                y_true, y_pred, metadata
            )
            results["error_analysis"] = error_analysis
        
        # Classification report
        report = classification_report(
            y_true, y_pred, target_names=LABEL_NAMES, output_dict=True
        )
        results["classification_report"] = report
        
        # Save results
        self.save_results(results, "evaluation_results.json")
        
        logger.info(f"Evaluation complete. Results saved to {self.output_dir}")
        return results
    
    def plot_confusion_matrix(
        self,
        cm: np.ndarray,
        filename: str,
        normalize: bool = True,
    ) -> None:
        """Plot and save confusion matrix."""
        if normalize:
            cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
            cm_display = cm_norm
            fmt = ".2f"
        else:
            cm_display = cm
            fmt = "d"
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm_display,
            annot=True,
            fmt=fmt,
            cmap="Blues",
            xticklabels=LABEL_NAMES,
            yticklabels=LABEL_NAMES,
            cbar_kws={"label": "Proportion" if normalize else "Count"},
        )
        plt.title("Confusion Matrix (Normalized)" if normalize else "Confusion Matrix")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()
        
        logger.info(f"Saved confusion matrix to {filename}")
    
    def analyze_calibration(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
    ) -> Dict:
        """Analyze model calibration (confidence vs accuracy)."""
        logger.info("Analyzing calibration...")
        
        results = {}
        
        # Get confidence (max probability for predicted class)
        confidences = np.max(y_proba, axis=1)
        predictions = np.argmax(y_proba, axis=1)
        correct = (predictions == y_true).astype(int)
        
        # Plot reliability diagram
        plt.figure(figsize=(10, 6))
        
        # Compute calibration curve
        fraction_of_positives, mean_predicted_value = calibration_curve(
            correct, confidences, n_bins=10, strategy="uniform"
        )
        
        plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
        plt.plot(
            mean_predicted_value,
            fraction_of_positives,
            marker="o",
            label="Model",
        )
        plt.xlabel("Mean Predicted Probability")
        plt.ylabel("Fraction of Positives")
        plt.title("Calibration Curve (Reliability Diagram)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "calibration_curve.png", dpi=300)
        plt.close()
        
        # Expected Calibration Error (ECE)
        ece = np.abs(fraction_of_positives - mean_predicted_value).mean()
        results["expected_calibration_error"] = float(ece)
        
        logger.info(f"Expected Calibration Error: {ece:.4f}")
        return results
    
    def analyze_confidence(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
    ) -> Dict:
        """Analyze prediction confidence."""
        logger.info("Analyzing prediction confidence...")
        
        confidences = np.max(y_proba, axis=1)
        correct = (y_pred == y_true).astype(int)
        
        results = {
            "mean_confidence": float(confidences.mean()),
            "std_confidence": float(confidences.std()),
            "mean_confidence_correct": float(confidences[correct == 1].mean()),
            "mean_confidence_incorrect": float(confidences[correct == 0].mean()),
        }
        
        # Plot confidence distribution
        plt.figure(figsize=(10, 6))
        plt.hist(
            confidences[correct == 1],
            bins=30,
            alpha=0.5,
            label="Correct",
            color="green",
        )
        plt.hist(
            confidences[correct == 0],
            bins=30,
            alpha=0.5,
            label="Incorrect",
            color="red",
        )
        plt.xlabel("Confidence")
        plt.ylabel("Frequency")
        plt.title("Confidence Distribution by Correctness")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "confidence_distribution.png", dpi=300)
        plt.close()
        
        return results
    
    def analyze_errors_by_source(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        metadata: pd.DataFrame,
    ) -> Dict:
        """Analyze prediction errors by source."""
        if "source_name" not in metadata.columns:
            logger.warning("No source_name in metadata, skipping error analysis")
            return {}
        
        logger.info("Analyzing errors by source...")
        
        df = metadata.copy()
        df["true_label"] = y_true
        df["pred_label"] = y_pred
        df["correct"] = (y_true == y_pred).astype(int)
        
        # Accuracy by source
        source_accuracy = df.groupby("source_name")["correct"].mean().sort_values()
        
        # Plot
        plt.figure(figsize=(12, 6))
        source_accuracy.plot(kind="barh")
        plt.xlabel("Accuracy")
        plt.ylabel("Source")
        plt.title("Prediction Accuracy by Source")
        plt.tight_layout()
        plt.savefig(self.output_dir / "accuracy_by_source.png", dpi=300)
        plt.close()
        
        return {
            "accuracy_by_source": source_accuracy.to_dict(),
            "worst_sources": source_accuracy.head(5).to_dict(),
            "best_sources": source_accuracy.tail(5).to_dict(),
        }
    
    def save_results(self, results: Dict, filename: str) -> None:
        """Save evaluation results to JSON."""
        import json
        
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to {output_path}")


def main():
    """Example usage."""
    # Simulated data for demonstration
    np.random.seed(42)
    n_samples = 1000
    
    y_true = np.random.randint(0, 5, n_samples)
    y_pred = y_true.copy()
    # Add some errors
    error_idx = np.random.choice(n_samples, size=int(n_samples * 0.2), replace=False)
    y_pred[error_idx] = np.random.randint(0, 5, len(error_idx))
    
    # Simulated probabilities
    y_proba = np.random.dirichlet(np.ones(5) * 5, n_samples)
    for i in range(n_samples):
        y_proba[i, y_pred[i]] = max(y_proba[i, y_pred[i]], 0.5)
    y_proba = y_proba / y_proba.sum(axis=1, keepdims=True)
    
    # Metadata
    metadata = pd.DataFrame({
        "source_name": np.random.choice(["CNN", "Fox News", "BBC", "NYT"], n_samples),
    })
    
    # Evaluate
    evaluator = ModelEvaluator()
    results = evaluator.evaluate(y_true, y_pred, y_proba, metadata)
    
    print("\nEvaluation Results:")
    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"F1 (macro): {results['f1_macro']:.4f}")
    print(f"Cohen's Kappa: {results['cohen_kappa']:.4f}")


if __name__ == "__main__":
    main()
