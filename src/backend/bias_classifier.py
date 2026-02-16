"""
Comprehensive political-bias classifier.

Ensembles two transformer models with additional evidence signals:
- Direction model (left / center / right)
- Intensity model (biased / non-biased)
- Ideological lexicon signal (left/right framing terms)
- Loaded-language intensity signal
- Source prior signal (optional, from source-assigned bias)

Outputs a 5-tier bias label with confidence and explanation fields.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from functools import lru_cache

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EnsembleConfig:
    """Tuneable thresholds and model identifiers."""

    direction_model_id: str = "bucketresearch/politicalBiasBERT"
    intensity_model_id: str = "himel7/bias-detector"

    # Primary model contributions.
    model_direction_weight: float = 0.65
    model_intensity_weight: float = 0.7

    # Auxiliary evidence contributions.
    lexical_direction_weight: float = 0.25
    source_prior_weight: float = 0.1
    lexical_intensity_weight: float = 0.3

    # Label decision thresholds.
    center_threshold: float = 0.52
    weak_direction_threshold: float = 0.17
    strong_direction_threshold: float = 0.40
    high_intensity_threshold: float = 0.62

    # Inference.
    batch_size: int = 8
    max_text_chars: int = 5000


DEFAULT_CONFIG = EnsembleConfig()

BIAS_LABELS = [
    "Left-Leaning",
    "Center-Left",
    "Centrist",
    "Center-Right",
    "Right-Leaning",
]

SOURCE_PRIOR_SCORE = {
    "left-leaning": -0.85,
    "center-left": -0.40,
    "centrist": 0.0,
    "center-right": 0.40,
    "right-leaning": 0.85,
    "unclassified": 0.0,
}

# Broad lexical signals (hand-curated phrase sets).
LEFT_TERMS = {
    "wealth tax",
    "living wage",
    "union organizing",
    "collective bargaining",
    "public option",
    "single payer",
    "medicare for all",
    "social safety net",
    "economic justice",
    "racial justice",
    "systemic racism",
    "climate justice",
    "green new deal",
    "gun control",
    "assault weapons ban",
    "reproductive rights",
    "pro-choice",
    "abortion access",
    "immigrant rights",
    "path to citizenship",
    "workers rights",
    "corporate greed",
    "income inequality",
    "fossil fuel companies",
    "police reform",
    "mass incarceration",
    "voter suppression",
    "lgbtq rights",
    "trans rights",
    "student debt relief",
    "affordable housing",
    "public education",
    "minimum wage hike",
    "diversity equity inclusion",
    "universal childcare",
    "food insecurity",
    "community investment",
    "social programs",
    "progressive",
    "liberal",
    "equity",
    "inclusion",
    "redistribution",
    "environmental justice",
    "civil liberties",
}

RIGHT_TERMS = {
    "border security",
    "illegal immigration",
    "law and order",
    "traditional values",
    "religious freedom",
    "second amendment",
    "gun rights",
    "tax cuts",
    "small government",
    "limited government",
    "free market",
    "energy independence",
    "drill baby drill",
    "family values",
    "parental rights",
    "school choice",
    "pro-life",
    "unborn child",
    "fiscal responsibility",
    "states rights",
    "election integrity",
    "voter fraud",
    "tough on crime",
    "patriot",
    "america first",
    "national sovereignty",
    "anti woke",
    "woke agenda",
    "cancel culture",
    "constitutional originalism",
    "deregulation",
    "job creators",
    "government overreach",
    "socialism",
    "radical left",
    "deep state",
    "meritocracy",
    "parental notification",
    "secure the border",
    "traditional marriage",
    "conservative",
    "freedom",
    "patriotic",
    "personal responsibility",
    "military strength",
}

LOADED_LANGUAGE_TERMS = {
    "outrageous",
    "shocking",
    "radical",
    "extremist",
    "dangerous",
    "reckless",
    "disastrous",
    "catastrophic",
    "weaponized",
    "corrupt",
    "dishonest",
    "lying",
    "traitor",
    "threat",
    "war on",
    "attack on",
    "destroy",
    "collapse",
    "crisis",
    "chaos",
    "scandal",
    "cover-up",
    "must",
    "never",
    "always",
    "clearly",
    "obviously",
    "undeniable",
    "propaganda",
    "fake news",
    "hoax",
    "witch hunt",
    "enemy",
    "disgrace",
    "betrayal",
    "absolutely",
    "no doubt",
    "without question",
    "evil",
    "fraudulent",
    "alarming",
    "horrific",
    "unacceptable",
    "devastating",
    "rigged",
}

BALANCE_TERMS = {
    "both sides",
    "according to data",
    "nonpartisan",
    "bipartisan",
    "independent analysis",
    "experts say",
    "fact check",
    "evidence suggests",
    "research shows",
    "in context",
}

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")
HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTI_SPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def preprocess_text(
    title: str,
    summary: str,
    content: str = "",
    max_chars: int = 5000,
) -> str:
    """Clean and combine title + summary + article content into one input string."""
    combined = " ".join(x for x in [title, summary, content] if x)
    combined = HTML_TAG_RE.sub(" ", combined)
    combined = MULTI_SPACE_RE.sub(" ", combined).strip()
    return combined[:max_chars]


# ---------------------------------------------------------------------------
# Cached model loaders
# ---------------------------------------------------------------------------


_direction_pipeline_cache = None
_intensity_pipeline_cache = None


def _load_direction_pipeline(model_id: str):
    global _direction_pipeline_cache
    if _direction_pipeline_cache is not None:
        return _direction_pipeline_cache
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    _direction_pipeline_cache = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        top_k=None,
        device=-1,
        truncation=True,
        max_length=512,
    )
    return _direction_pipeline_cache


def _load_intensity_pipeline(model_id: str):
    global _intensity_pipeline_cache
    if _intensity_pipeline_cache is not None:
        return _intensity_pipeline_cache
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    _intensity_pipeline_cache = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        top_k=None,
        device=-1,
        truncation=True,
        max_length=512,
    )
    return _intensity_pipeline_cache


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------


class PoliticalBiasClassifier:
    """Comprehensive ensemble classifier that adds ML bias columns to a DataFrame."""

    def __init__(self, config: EnsembleConfig | None = None) -> None:
        self.cfg = config or DEFAULT_CONFIG

    @property
    def direction_pipe(self):
        return _load_direction_pipeline(self.cfg.direction_model_id)

    @property
    def intensity_pipe(self):
        return _load_intensity_pipeline(self.cfg.intensity_model_id)

    def _run_pipeline_batched(
        self,
        pipe,
        texts: list[str],
        progress_callback: Optional[Callable[[float], None]] = None,
        progress_offset: float = 0.0,
        progress_span: float = 0.5,
    ) -> list[dict[str, float]]:
        """Run a HF pipeline in batches and return [{label: prob, …}, …]."""
        if not texts:
            return []

        results: list[dict[str, float]] = []
        bs = self.cfg.batch_size
        n = len(texts)

        for start in range(0, n, bs):
            batch = texts[start : start + bs]
            batch_out = pipe(batch)
            for item in batch_out:
                results.append({d["label"]: d["score"] for d in item})
            if progress_callback:
                frac = progress_offset + progress_span * min((start + bs) / n, 1.0)
                progress_callback(frac)

        return results

    def _normalize_direction_probs(self, raw_probs: dict[str, float]) -> dict[str, float]:
        """Map model output labels to canonical left/center/right probabilities."""
        mapped = {"left": 0.0, "center": 0.0, "right": 0.0}

        for label, score in raw_probs.items():
            key = str(label).strip().lower()
            if any(tok in key for tok in ["left", "liberal", "progressive", "democrat"]):
                mapped["left"] += score
            elif any(tok in key for tok in ["right", "conservative", "republican"]):
                mapped["right"] += score
            elif any(tok in key for tok in ["center", "centre", "neutral", "moderate"]):
                mapped["center"] += score

        if mapped["left"] + mapped["center"] + mapped["right"] == 0:
            # Common fallback for generic class labels (LABEL_0/1/2):
            # assume sorted order is left, center, right.
            items = sorted(raw_probs.items(), key=lambda kv: kv[0])
            if len(items) >= 3:
                mapped["left"] = items[0][1]
                mapped["center"] = items[1][1]
                mapped["right"] = items[2][1]
            elif len(items) == 2:
                mapped["left"] = items[0][1]
                mapped["right"] = items[1][1]

        total = mapped["left"] + mapped["center"] + mapped["right"]
        if total <= 0:
            return {"left": 0.33, "center": 0.34, "right": 0.33}

        return {k: v / total for k, v in mapped.items()}

    def _normalize_intensity_prob(self, raw_probs: dict[str, float]) -> float:
        """Extract P(Biased) from model output labels."""
        p_biased = 0.0
        p_non_biased = 0.0

        for label, score in raw_probs.items():
            key = str(label).strip().lower()
            if ("non" in key and "bias" in key) or "unbiased" in key:
                p_non_biased += score
            elif any(tok in key for tok in ["biased", "bias", "partisan", "propaganda"]):
                p_biased += score

        if p_biased == 0 and p_non_biased == 0:
            items = sorted(raw_probs.items(), key=lambda kv: kv[0])
            if len(items) == 2:
                # Fallback for binary generic labels.
                p_non_biased = items[0][1]
                p_biased = items[1][1]
            elif items:
                p_biased = max(items, key=lambda kv: kv[1])[1]

        total = p_biased + p_non_biased
        if total > 0:
            p_biased /= total

        return max(0.0, min(1.0, p_biased))

    @staticmethod
    def _count_term_hits(text_lower: str, token_counts: Counter, terms: set[str]) -> int:
        hits = 0
        for term in terms:
            if " " in term or "-" in term:
                hits += text_lower.count(term)
            else:
                hits += token_counts.get(term, 0)
        return hits

    def _analyze_lexical_signals(self, text: str) -> dict[str, float]:
        text_lower = text.lower()
        tokens = WORD_RE.findall(text_lower)
        token_counts = Counter(tokens)
        token_count = max(1, len(tokens))

        left_hits = self._count_term_hits(text_lower, token_counts, LEFT_TERMS)
        right_hits = self._count_term_hits(text_lower, token_counts, RIGHT_TERMS)
        loaded_hits = self._count_term_hits(text_lower, token_counts, LOADED_LANGUAGE_TERMS)
        balance_hits = self._count_term_hits(text_lower, token_counts, BALANCE_TERMS)

        # Raw ideology direction in [-1, 1], right-positive.
        directional_raw = (right_hits - left_hits) / (left_hits + right_hits + 2)

        # Balance cues suppress directional certainty.
        balance_damp = min(0.4, 0.07 * balance_hits)
        directional_score = directional_raw * (1 - balance_damp)

        # Extra rhetorical intensity cues from punctuation and all-caps words.
        exclamation_hits = text.count("!")
        all_caps_hits = sum(
            1
            for raw in text.split()
            if len(raw) >= 4 and raw.isupper() and raw.isalpha()
        )

        loaded_signal = loaded_hits + 0.5 * exclamation_hits + 0.8 * all_caps_hits
        intensity_score = min(
            1.0,
            loaded_signal / max(3.0, token_count / 22.0),
        )

        return {
            "left_hits": float(left_hits),
            "right_hits": float(right_hits),
            "loaded_hits": float(loaded_hits),
            "balance_hits": float(balance_hits),
            "direction_score": float(max(-1.0, min(1.0, directional_score))),
            "intensity_score": float(intensity_score),
            "token_count": float(token_count),
        }

    @staticmethod
    def _source_prior(source_bias: str) -> float:
        if not source_bias:
            return 0.0
        return SOURCE_PRIOR_SCORE.get(str(source_bias).strip().lower(), 0.0)

    @staticmethod
    def _normalize_triplet(left: float, center: float, right: float) -> tuple[float, float, float]:
        left = max(0.0, left)
        center = max(0.0, center)
        right = max(0.0, right)
        total = left + center + right
        if total <= 0:
            return 0.33, 0.34, 0.33
        return left / total, center / total, right / total

    def _combine(
        self,
        direction_probs: dict[str, float],
        intensity_probs: dict[str, float],
        lexical: dict[str, float],
        source_bias: str,
    ) -> dict[str, float | str]:
        """Combine model and heuristic signals into final outputs."""
        cfg = self.cfg

        dir_norm = self._normalize_direction_probs(direction_probs)
        p_left = dir_norm["left"]
        p_center = dir_norm["center"]
        p_right = dir_norm["right"]

        p_biased_model = self._normalize_intensity_prob(intensity_probs)

        lexical_direction = lexical["direction_score"]
        lexical_intensity = lexical["intensity_score"]
        source_prior = self._source_prior(source_bias)

        model_direction = p_right - p_left

        weighted_direction = (
            cfg.model_direction_weight * model_direction
            + cfg.lexical_direction_weight * lexical_direction
            + cfg.source_prior_weight * source_prior
        )
        weight_total = (
            cfg.model_direction_weight
            + cfg.lexical_direction_weight
            + cfg.source_prior_weight
        )
        direction_score = weighted_direction / max(weight_total, 1e-6)

        # Strong center probability suppresses direction magnitude.
        direction_score *= 1 - 0.30 * p_center
        direction_score = max(-1.0, min(1.0, direction_score))

        bias_intensity = (
            cfg.model_intensity_weight * p_biased_model
            + cfg.lexical_intensity_weight * lexical_intensity
        ) / max(cfg.model_intensity_weight + cfg.lexical_intensity_weight, 1e-6)
        bias_intensity = max(0.0, min(1.0, bias_intensity))

        direction_strength = abs(direction_score)

        if (
            p_center >= cfg.center_threshold
            and direction_strength < cfg.weak_direction_threshold
            and bias_intensity < cfg.high_intensity_threshold
        ):
            label = "Centrist"
        elif direction_score <= -cfg.strong_direction_threshold or (
            direction_score < -cfg.weak_direction_threshold
            and bias_intensity >= cfg.high_intensity_threshold
        ):
            label = "Left-Leaning"
        elif direction_score >= cfg.strong_direction_threshold or (
            direction_score > cfg.weak_direction_threshold
            and bias_intensity >= cfg.high_intensity_threshold
        ):
            label = "Right-Leaning"
        elif direction_score < 0:
            label = "Center-Left"
        elif direction_score > 0:
            label = "Center-Right"
        else:
            label = "Centrist"

        # Consensus-based confidence.
        consensus_signals = [model_direction]
        if lexical["left_hits"] + lexical["right_hits"] > 0:
            consensus_signals.append(lexical_direction)
        if source_prior != 0:
            consensus_signals.append(source_prior)

        consensus = abs(sum(consensus_signals) / len(consensus_signals))
        evidence = 0.45 * direction_strength + 0.35 * bias_intensity + 0.20 * abs(model_direction)
        center_fit = p_center if label == "Centrist" else 1 - p_center

        confidence = 0.15 + 0.5 * evidence + 0.2 * consensus + 0.15 * center_fit
        confidence = max(0.05, min(0.99, confidence))

        # Spectrum values blend model output with auxiliary evidence.
        left_adj = p_left + max(0.0, -lexical_direction) * 0.15 + max(0.0, -source_prior) * 0.08
        right_adj = p_right + max(0.0, lexical_direction) * 0.15 + max(0.0, source_prior) * 0.08
        center_adj = p_center + (1 - abs(lexical_direction)) * 0.05
        spec_left, spec_center, spec_right = self._normalize_triplet(left_adj, center_adj, right_adj)

        source_display = source_bias if source_bias else "Unclassified"
        explanation = (
            f"Model L/C/R={p_left:.2f}/{p_center:.2f}/{p_right:.2f}; "
            f"lexical hits L/R={int(lexical['left_hits'])}/{int(lexical['right_hits'])}; "
            f"loaded terms={int(lexical['loaded_hits'])}; "
            f"source prior={source_display}; "
            f"direction={direction_score:+.2f}, intensity={bias_intensity:.2f}."
        )

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "spectrum_left": round(spec_left, 4),
            "spectrum_center": round(spec_center, 4),
            "spectrum_right": round(spec_right, 4),
            "bias_intensity": round(bias_intensity, 4),
            "direction_score": round(direction_score, 4),
            "direction_strength": round(direction_strength, 4),
            "model_left_prob": round(p_left, 4),
            "model_center_prob": round(p_center, 4),
            "model_right_prob": round(p_right, 4),
            "model_biased_prob": round(p_biased_model, 4),
            "lexical_left_hits": int(lexical["left_hits"]),
            "lexical_right_hits": int(lexical["right_hits"]),
            "loaded_language_hits": int(lexical["loaded_hits"]),
            "balance_hits": int(lexical["balance_hits"]),
            "source_prior_score": round(source_prior, 4),
            "explanation": explanation,
        }

    def classify_dataframe(
        self,
        df: pd.DataFrame,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> pd.DataFrame:
        """
        Classify every row in *df* and return a copy with additional columns.

        Required columns: title, summary (content optional, source bias optional).
        """
        if df.empty:
            out = df.copy()
            if progress_callback:
                progress_callback(1.0)
            return out

        texts = [
            preprocess_text(
                str(row.get("title", "")),
                str(row.get("summary", "")),
                str(row.get("content", "")),
                self.cfg.max_text_chars,
            )
            for _, row in df.iterrows()
        ]

        texts = [t if t.strip() else "No content available." for t in texts]

        direction_results = self._run_pipeline_batched(
            self.direction_pipe,
            texts,
            progress_callback,
            progress_offset=0.0,
            progress_span=0.35,
        )
        intensity_results = self._run_pipeline_batched(
            self.intensity_pipe,
            texts,
            progress_callback,
            progress_offset=0.35,
            progress_span=0.35,
        )

        combined_rows = []
        total = len(texts)
        for idx, (text, dir_p, int_p) in enumerate(
            zip(texts, direction_results, intensity_results)
        ):
            lexical = self._analyze_lexical_signals(text)
            source_bias = str(df.iloc[idx].get("political_bias", "Unclassified"))
            combined_rows.append(self._combine(dir_p, int_p, lexical, source_bias))

            if progress_callback:
                frac = 0.70 + 0.30 * ((idx + 1) / total)
                progress_callback(frac)

        out = df.copy()
        out["ml_bias"] = [r["label"] for r in combined_rows]
        out["ml_confidence"] = [r["confidence"] for r in combined_rows]
        out["spectrum_left"] = [r["spectrum_left"] for r in combined_rows]
        out["spectrum_center"] = [r["spectrum_center"] for r in combined_rows]
        out["spectrum_right"] = [r["spectrum_right"] for r in combined_rows]
        out["bias_intensity"] = [r["bias_intensity"] for r in combined_rows]

        out["ml_direction_score"] = [r["direction_score"] for r in combined_rows]
        out["ml_direction_strength"] = [r["direction_strength"] for r in combined_rows]
        out["ml_model_left_prob"] = [r["model_left_prob"] for r in combined_rows]
        out["ml_model_center_prob"] = [r["model_center_prob"] for r in combined_rows]
        out["ml_model_right_prob"] = [r["model_right_prob"] for r in combined_rows]
        out["ml_model_biased_prob"] = [r["model_biased_prob"] for r in combined_rows]
        out["ml_lexical_left_hits"] = [r["lexical_left_hits"] for r in combined_rows]
        out["ml_lexical_right_hits"] = [r["lexical_right_hits"] for r in combined_rows]
        out["ml_loaded_language_hits"] = [r["loaded_language_hits"] for r in combined_rows]
        out["ml_balance_hits"] = [r["balance_hits"] for r in combined_rows]
        out["ml_source_prior_score"] = [r["source_prior_score"] for r in combined_rows]
        out["ml_explanation"] = [r["explanation"] for r in combined_rows]

        if progress_callback:
            progress_callback(1.0)

        return out
