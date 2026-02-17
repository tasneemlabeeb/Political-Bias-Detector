"""
ML Inference Service for Political Bias Detection.

Loads the fine-tuned RoBERTa model trained on 3 Kaggle datasets.
Drop-in replacement for Gemini-based classification in llm_service.py.
"""

import logging
import os
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

LABEL_MAP = {
    0: "Left-Leaning",
    1: "Center-Left",
    2: "Centrist",
    3: "Center-Right",
    4: "Right-Leaning",
}


class MLBiasClassifier:
    """Production ML classifier using fine-tuned transformer model."""

    def __init__(self, model_path: str = "models/custom_bias_detector"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self._load_model()

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_model(self):
        """Load model and tokenizer from disk."""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model not found at {self.model_path}. ML classification disabled.")
            return

        logger.info(f"Loading ML model from {self.model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"ML model loaded on {self.device}")

    @property
    def is_available(self) -> bool:
        return self.model is not None

    @torch.no_grad()
    def classify(self, text: str, title: str = "") -> Dict:
        """
        Classify text for political bias.

        Returns dict matching existing API format:
        {ml_bias, ml_confidence, ml_reasoning, spectrum_scores}
        """
        if not self.is_available:
            return {"ml_bias": "Centrist", "ml_confidence": 0.0, "ml_reasoning": "ML model not loaded"}

        full_text = f"{title} {text}".strip() if title else text

        encoding = self.tokenizer(
            full_text,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**encoding)
        probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

        predicted_class = int(probs.argmax())
        confidence = float(probs[predicted_class])
        bias_label = LABEL_MAP[predicted_class]

        # Spectrum scores for frontend visualization
        spectrum_left = float(probs[0] + probs[1])
        spectrum_center = float(probs[2])
        spectrum_right = float(probs[3] + probs[4])

        # Bias intensity: how far from center (0=centrist, 1=extreme)
        expected = sum(float(probs[i]) * i for i in range(5))
        bias_intensity = abs(expected - 2.0) / 2.0

        return {
            "ml_bias": bias_label,
            "ml_confidence": round(confidence, 4),
            "ml_reasoning": f"ML model prediction: {bias_label} with {confidence:.1%} confidence",
            "spectrum_left": round(spectrum_left, 4),
            "spectrum_center": round(spectrum_center, 4),
            "spectrum_right": round(spectrum_right, 4),
            "bias_intensity": round(bias_intensity, 4),
            "all_probabilities": {LABEL_MAP[i]: round(float(probs[i]), 4) for i in range(5)},
        }

    @torch.no_grad()
    def classify_batch(self, texts: List[str], titles: Optional[List[str]] = None) -> List[Dict]:
        """Classify multiple texts efficiently in a single forward pass."""
        if not self.is_available:
            return [{"ml_bias": "Centrist", "ml_confidence": 0.0, "ml_reasoning": "ML model not loaded"}] * len(texts)

        if titles is None:
            titles = [""] * len(texts)

        full_texts = [f"{t} {text}".strip() if t else text for t, text in zip(titles, texts)]

        encodings = self.tokenizer(
            full_texts,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**encodings)
        all_probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

        results = []
        for probs in all_probs:
            predicted_class = int(probs.argmax())
            confidence = float(probs[predicted_class])
            bias_label = LABEL_MAP[predicted_class]

            spectrum_left = float(probs[0] + probs[1])
            spectrum_center = float(probs[2])
            spectrum_right = float(probs[3] + probs[4])

            expected = sum(float(probs[i]) * i for i in range(5))
            bias_intensity = abs(expected - 2.0) / 2.0

            results.append({
                "ml_bias": bias_label,
                "ml_confidence": round(confidence, 4),
                "ml_reasoning": f"ML model: {bias_label} ({confidence:.1%})",
                "spectrum_left": round(spectrum_left, 4),
                "spectrum_center": round(spectrum_center, 4),
                "spectrum_right": round(spectrum_right, 4),
                "bias_intensity": round(float(bias_intensity), 4),
            })

        return results


# Singleton instance
_ml_classifier = None


def get_ml_classifier() -> MLBiasClassifier:
    """Get or create the global ML classifier instance."""
    global _ml_classifier
    if _ml_classifier is None:
        model_path = os.getenv("MODEL_DIRECTION_PATH", "models/custom_bias_detector")
        _ml_classifier = MLBiasClassifier(model_path=model_path)
    return _ml_classifier
