import logging
from typing import List, Tuple
import config

logger = logging.getLogger(__name__)

class BERTClassifier:
    """
    Singleton class to manage the BERT Zero-Shot classification model.
    Loads the model once and uses a keyword-based heuristic fallback if model loading fails.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BERTClassifier, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.model_name = config.BERT_MODEL_NAME
        self.pipeline = None
        self.use_fallback = False
        self._load_model()
        self._initialized = True

    def _load_model(self):
        try:
            # Import inside function to allow application startup even if imports fail
            from transformers import pipeline
            import torch
            
            # Autodetect CUDA / GPU
            device = 0 if torch.cuda.is_available() else -1
            
            logger.info(f"Attempting to load BERT model: {self.model_name} on device: {'GPU' if device == 0 else 'CPU'}")
            
            # Using zero-shot classification pipeline
            self.pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=device
            )
            self.use_fallback = False
            logger.info("BERT classifier model loaded successfully.")
        except Exception as e:
            self.use_fallback = True
            logger.error(f"Failed to load BERT classifier model ({e}). Reverting to keyword heuristic.")

    def classify_article(self, title: str, description: str, candidate_labels: List[str]) -> Tuple[str, float]:
        """
        Classifies an article into one of the candidate labels (industries).
        Returns a tuple of (predicted_industry, confidence_score).
        """
        text = f"{title or ''} {description or ''}".strip()
        if not text:
            return "Unclassified", 0.0

        if not self.use_fallback and self.pipeline is not None:
            try:
                # Run the model inference
                result = self.pipeline(text, candidate_labels, multi_label=False)
                predicted_label = result['labels'][0]
                confidence = result['scores'][0]
                return predicted_label, float(confidence)
            except Exception as e:
                logger.error(f"Error during BERT inference: {e}. Reverting to fallback classifier.")

        # Fallback to keyword-based heuristic classification
        return self._heuristic_classify(text, candidate_labels)

    def _heuristic_classify(self, text: str, candidate_labels: List[str]) -> Tuple[str, float]:
        """
        Heuristic fallback using keyword scoring.
        Differentiates between highly specific and generic keywords.
        """
        text_lower = text.lower()
        
        # Define generic keywords that are too common to establish a high confidence by themselves
        generic_keywords = {
            "home", "offer", "products", "product", "tech", "techs", 
            "style", "learning", "meal", "supplement", "personal care"
        }
        
        best_industry = "Unclassified"
        best_score = 0.0
        
        for label in candidate_labels:
            keywords = config.INDUSTRY_KEYWORDS.get(label, [])
            score = 0.0
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in text_lower:
                    if kw_lower in generic_keywords:
                        score += 0.5  # generic keywords get low weight
                    else:
                        score += 2.0  # specific keywords get high weight
            
            if score > best_score:
                best_score = score
                best_industry = label
                
        if best_score > 0:
            # Calculate confidence based on the score
            if best_score <= 0.5:
                # Only 1 generic keyword matched, confidence is 0.25 (below threshold 0.4)
                confidence = 0.25
            elif best_score <= 1.0:
                # 2 generic keywords matched, confidence is 0.35 (below threshold 0.4)
                confidence = 0.35
            elif best_score <= 2.0:
                # 1 specific keyword matched, confidence is 0.75 (above threshold 0.4)
                confidence = 0.75
            else:
                # Multiple matches or combination, confidence is high
                confidence = 0.95
            return best_industry, confidence
            
        return "Unclassified", 0.0
