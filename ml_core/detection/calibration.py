from typing import List
import numpy as np

try:
    from sklearn.isotonic import IsotonicRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class ConfidenceCalibrator:
    def __init__(self):
        if HAS_SKLEARN:
            self.iso_reg = IsotonicRegression(out_of_bounds='clip')
        else:
            self.iso_reg = None
        self.is_fitted = False
        
    def fit(self, raw_scores: List[float], true_labels: List[int]):
        """
        Fits the calibrator using isotonic regression.
        raw_scores: Model outputs (e.g., softmax probabilities for contradiction)
        true_labels: Binary labels (1 for contradiction, 0 for not)
        """
        if not HAS_SKLEARN:
            return
            
        self.iso_reg.fit(raw_scores, true_labels)
        self.is_fitted = True
        
    def calibrate(self, raw_score: float) -> float:
        """
        Applies the calibration function.
        """
        if not self.is_fitted or not HAS_SKLEARN:
            return float(raw_score)
            
        return float(self.iso_reg.predict([raw_score])[0])

# Global instance for the pipeline to use
calibrator = ConfidenceCalibrator()
