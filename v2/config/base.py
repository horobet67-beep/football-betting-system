"""
Base configuration dataclasses for the v2 football betting system.
Provides typed configuration with clear contracts and defaults.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class PatternCategory(Enum):
    """Pattern categories for betting patterns."""
    GOALS = "goals"
    CORNERS = "corners"
    CARDS = "cards"


@dataclass
class CoreConfig:
    """Core system configuration."""
    # Data paths
    data_dir: str = "data"
    results_dir: str = "results"
    cache_dir: str = "cache"
    
    # Processing
    random_seed: int = 42
    n_jobs: int = -1
    
    # Feature engineering
    rolling_window_days: int = 14
    min_team_matches: int = 5
    
    # Walk-forward settings
    walkforward_test_days: int = 7
    min_training_days: int = 90


@dataclass
class ThresholdConfig:
    """Pattern threshold configuration."""
    # Global minimums
    min_matches: int = 20
    min_accuracy: float = 0.55
    min_coverage: float = 0.05
    max_coverage: float = 0.95
    
    # Category-specific confidence thresholds
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        PatternCategory.GOALS.value: 0.65,
        PatternCategory.CORNERS.value: 0.60,
        PatternCategory.CARDS.value: 0.70
    })
    
    # Dynamic threshold learning
    use_dynamic_thresholds: bool = False
    threshold_learning_window: int = 30


@dataclass
class ModelConfig:
    """Model training configuration."""
    # Model selection
    use_ensemble: bool = False
    use_stacking: bool = False
    use_calibration: bool = False
    
    # SMOTE settings
    use_smote: bool = False
    smote_imbalance_threshold: float = 0.3
    
    # Cross-validation
    cv_folds: int = 5
    stratify_cv: bool = True
    
    # Feature selection
    use_feature_subsets: bool = False
    feature_subset_size: Optional[float] = 0.8


@dataclass
class ProfitabilityConfig:
    """Profitability scoring weights."""
    accuracy_weight: float = 0.50
    precision_weight: float = 0.20
    coverage_weight: float = 0.20
    event_rate_penalty: float = 0.10
    
    # Optional variance penalty (defer to Phase 2)
    use_variance_penalty: bool = False
    variance_weight: float = 0.0


@dataclass
class Config:
    """Complete system configuration."""
    core: CoreConfig = field(default_factory=CoreConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    profitability: ProfitabilityConfig = field(default_factory=ProfitabilityConfig)
    
    # League-specific overrides
    league_name: Optional[str] = None
    league_overrides: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Apply league-specific overrides after initialization."""
        if self.league_name and self.league_overrides:
            league_config = self.league_overrides.get(self.league_name, {})
            for section, overrides in league_config.items():
                if hasattr(self, section):
                    section_config = getattr(self, section)
                    for key, value in overrides.items():
                        if hasattr(section_config, key):
                            setattr(section_config, key, value)
