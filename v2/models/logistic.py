"""
Simple logistic regression trainer for pattern prediction.
MVP implementation focusing on clarity and speed.
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Results from model training."""
    pattern_name: str
    team_name: str
    n_samples: int
    n_positive: int
    feature_names: list
    model_params: Dict[str, Any]
    cv_scores: Optional[Dict[str, float]] = None


class SimpleLogisticTrainer:
    """
    Simple logistic regression trainer.
    
    Provides MVP functionality without complex ensembles or stacking.
    Focus on speed and interpretability.
    """
    
    def __init__(
        self,
        random_state: int = 42,
        max_iter: int = 1000,
        class_weight: Optional[str] = 'balanced',
        C: float = 1.0
    ):
        """
        Initialize trainer.
        
        Args:
            random_state: Random seed for reproducibility
            max_iter: Maximum iterations for solver
            class_weight: Class weighting strategy
            C: Regularization strength (smaller = more regularization)
        """
        self.random_state = random_state
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.C = C
        self.is_fitted = False
        self._model = None
        self._feature_names = None
        self._training_result = None
    
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        pattern_name: str,
        team_name: str,
        validate: bool = True
    ) -> 'SimpleLogisticTrainer':
        """
        Fit logistic regression model.
        
        Args:
            X: Feature matrix
            y: Target labels (boolean)
            pattern_name: Name of the pattern being trained
            team_name: Name of the team
            validate: Whether to run validation checks
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If input validation fails
        """
        if validate:
            self._validate_inputs(X, y)
        
        # Store feature names
        self._feature_names = list(X.columns)
        
        # Convert to numpy for sklearn compatibility
        X_array = X.values
        y_array = y.values.astype(bool)
        
        # Check for sufficient positive samples
        n_positive = np.sum(y_array)
        if n_positive < 2:
            logger.warning(f"Only {n_positive} positive samples for {team_name}/{pattern_name}")
            # Create dummy model that predicts minority class
            self._create_dummy_model(X_array, y_array, pattern_name, team_name)
            return self
        
        try:
            # Import sklearn here to avoid import errors if not installed
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            
            # Create pipeline with scaling
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(
                    random_state=self.random_state,
                    max_iter=self.max_iter,
                    class_weight=self.class_weight,
                    C=self.C
                ))
            ])
            
            # Fit model
            pipeline.fit(X_array, y_array)
            self._model = pipeline
            
            # Store training results
            self._training_result = TrainingResult(
                pattern_name=pattern_name,
                team_name=team_name,
                n_samples=len(X),
                n_positive=n_positive,
                feature_names=self._feature_names,
                model_params={
                    'C': self.C,
                    'class_weight': self.class_weight,
                    'random_state': self.random_state
                }
            )
            
            self.is_fitted = True
            logger.debug(f"Trained model for {team_name}/{pattern_name}: {len(X)} samples, {n_positive} positive")
            
        except ImportError:
            logger.error("scikit-learn not installed. Cannot train models.")
            raise
        except Exception as e:
            logger.error(f"Training failed for {team_name}/{pattern_name}: {e}")
            # Create dummy model as fallback
            self._create_dummy_model(X_array, y_array, pattern_name, team_name)
        
        return self
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of shape (n_samples, 2) with [P(negative), P(positive)]
            
        Raises:
            ValueError: If model not fitted or feature mismatch
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        if list(X.columns) != self._feature_names:
            raise ValueError("Feature names do not match training data")
        
        X_array = X.values
        
        if hasattr(self._model, 'predict_proba'):
            return self._model.predict_proba(X_array)
        else:
            # Dummy model case
            n_samples = len(X)
            proba = np.full((n_samples, 2), [0.8, 0.2])  # Conservative probabilities
            return proba
    
    def get_feature_importance(self) -> Optional[pd.Series]:
        """
        Get feature coefficients (importance) from logistic regression.
        
        Returns:
            Series with feature names and coefficients, or None if not available
        """
        if not self.is_fitted or not hasattr(self._model, 'named_steps'):
            return None
        
        try:
            # Extract coefficients from the classifier step
            classifier = self._model.named_steps['classifier']
            if hasattr(classifier, 'coef_'):
                coefficients = classifier.coef_[0]  # Binary classification
                return pd.Series(coefficients, index=self._feature_names)
        except Exception:
            pass
        
        return None
    
    def get_training_result(self) -> Optional[TrainingResult]:
        """Get training results summary."""
        return self._training_result
    
    def _validate_inputs(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Validate training inputs."""
        if len(X) != len(y):
            raise ValueError(f"X and y must have same length: {len(X)} vs {len(y)}")
        
        if len(X) < 5:
            raise ValueError(f"Insufficient samples for training: {len(X)}")
        
        if X.isnull().any().any():
            raise ValueError("X contains null values")
        
        if y.isnull().any():
            raise ValueError("y contains null values")
        
        # Check for constant features
        constant_features = X.columns[X.nunique() <= 1]
        if len(constant_features) > 0:
            logger.warning(f"Constant features detected: {list(constant_features)}")
    
    def _create_dummy_model(self, X: np.ndarray, y: np.ndarray, pattern_name: str, team_name: str) -> None:
        """Create dummy model for edge cases."""
        n_positive = np.sum(y)
        
        # Simple dummy that predicts based on class frequency
        class DummyModel:
            def __init__(self, positive_rate):
                self.positive_rate = positive_rate
            
            def predict_proba(self, X):
                n_samples = len(X)
                neg_prob = 1 - self.positive_rate
                pos_prob = self.positive_rate
                return np.full((n_samples, 2), [neg_prob, pos_prob])
        
        positive_rate = max(0.01, min(0.99, n_positive / len(y)))  # Clamp to reasonable range
        self._model = DummyModel(positive_rate)
        
        self._training_result = TrainingResult(
            pattern_name=pattern_name,
            team_name=team_name,
            n_samples=len(X),
            n_positive=n_positive,
            feature_names=self._feature_names,
            model_params={'type': 'dummy', 'positive_rate': positive_rate}
        )
        
        self.is_fitted = True
        logger.warning(f"Created dummy model for {team_name}/{pattern_name}")


def train_pattern_model(
    features_df: pd.DataFrame,
    labels: pd.Series,
    pattern_name: str,
    team_name: str,
    config: Optional[Dict[str, Any]] = None
) -> SimpleLogisticTrainer:
    """
    Convenience function to train a pattern model.
    
    Args:
        features_df: Feature matrix
        labels: Target labels
        pattern_name: Name of the pattern
        team_name: Name of the team
        config: Optional model configuration
        
    Returns:
        Trained model
    """
    if config is None:
        config = {}
    
    trainer = SimpleLogisticTrainer(**config)
    return trainer.fit(features_df, labels, pattern_name, team_name)
