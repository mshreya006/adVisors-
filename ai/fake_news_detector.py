import logging
import re
from typing import Tuple
import config

logger = logging.getLogger(__name__)

class FakeNewsDetector:
    """
    Singleton class to manage the Fake News Detection model.
    Loads a lightweight pre-trained transformer model once and uses a heuristic fallback if loading fails.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FakeNewsDetector, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.model_name = config.FAKE_NEWS_MODEL_NAME
        self.pipeline = None
        self.use_fallback = False
        self.label_mapping = {
            "LABEL_0": "Fake",
            "LABEL_1": "Real",
            "FAKE": "Fake",
            "REAL": "Real",
            "TRUE": "Real"
        }
        self._load_model()
        self._initialized = True

    def _load_model(self):
        try:
            from transformers import pipeline
            import torch
            
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Attempting to load Fake News model: {self.model_name} on device: {'GPU' if device == 0 else 'CPU'}")
            
            self.pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                device=device
            )
            self.use_fallback = False
            
            # Inspect actual id2label in pipeline if available
            if hasattr(self.pipeline, "model") and hasattr(self.pipeline.model, "config") and hasattr(self.pipeline.model.config, "id2label"):
                id2label = self.pipeline.model.config.id2label
                if id2label:
                    # e.g., {0: 'LABEL_0', 1: 'LABEL_1'} or {0: 'FAKE', 1: 'REAL'}
                    for idx, label in id2label.items():
                        clean_label = str(label).upper()
                        if "FAKE" in clean_label or "LABEL_0" in clean_label:
                            self.label_mapping[str(label)] = "Fake"
                            self.label_mapping[idx] = "Fake"
                        else:
                            self.label_mapping[str(label)] = "Real"
                            self.label_mapping[idx] = "Real"
                            
            logger.info("Fake News detector model loaded successfully.")
        except Exception as e:
            self.use_fallback = True
            logger.error(f"Failed to load Fake News detector model ({e}). Reverting to clickbait/linguistic heuristic.")

    def detect_fake_news(self, title: str, description: str) -> Tuple[str, float]:
        """
        Predicts if an article is Real or Fake news.
        Returns a tuple of (prediction_label, confidence_score).
        """
        text = f"{title or ''} {description or ''}".strip()
        if not text:
            return "Real", 0.5

        if not self.use_fallback and self.pipeline is not None:
            try:
                # Run text classification (truncate if text is extremely long)
                result = self.pipeline(text[:512])[0]
                raw_label = result['label']
                score = result['score']
                
                # Map raw label (e.g. LABEL_0, LABEL_1, FAKE, REAL) to Fake/Real
                mapped_label = self.label_mapping.get(raw_label, "Fake" if "0" in str(raw_label) else "Real")
                return mapped_label, float(score)
            except Exception as e:
                logger.error(f"Error during Fake News model inference: {e}. Reverting to fallback.")

        # Heuristic/Clickbait linguistic check fallback
        return self._heuristic_detect(title, description)

    def _heuristic_detect(self, title: str, description: str) -> Tuple[str, float]:
        """
        Heuristic fallback model. Analyze sensationalism, clickbait patterns, and structure.
        """
        title = title or ""
        desc = description or ""
        full_text = f"{title} {desc}"
        
        score = 0.0
        
        # 1. Clickbait/Sensational keywords
        sensational_words = [
            r"\bshocking\b", r"\bunbelievable\b", r"\byou won't believe\b", 
            r"\bweird trick\b", r"\bmiracle\b", r"\bsecret\b", r"\bconspiracy\b",
            r"\bbreaking news\b", r"\bviral\b", r"\bexposed!\b", r"\bscandalous\b"
        ]
        for pattern in sensational_words:
            if re.search(pattern, full_text, re.IGNORECASE):
                score += 0.25
                
        # 2. Capitalization check (e.g., all caps words in title like BREAKING, SHOCKING)
        caps_words = re.findall(r"\b[A-Z]{3,}\b", title)
        # Exclude legitimate short acronyms like US, AI, UK, IT
        filtered_caps = [w for w in caps_words if w not in ["USA", "US", "UK", "AI", "IT", "CEO", "UN", "EU"]]
        if len(filtered_caps) >= 2:
            score += 0.2
            
        # 3. Excessive exclamation marks
        if title.count("!") >= 2 or desc.count("!") >= 3:
            score += 0.15

        # 4. Short title / description with vague details
        if len(title) < 15 or len(desc) < 25:
            score += 0.1
            
        # Make final classification
        # If the sensationalism score is high, classify as Fake, else Real
        if score >= 0.35:
            # High clickbait score = Fake
            confidence = min(0.5 + score, 0.9)
            return "Fake", confidence
        else:
            # Low clickbait score = Real
            confidence = min(0.6 + (0.35 - score), 0.95)
            return "Real", confidence
