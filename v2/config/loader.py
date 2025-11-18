"""
Configuration loader with layered overrides: global → league → CLI.
Provides clean interface for merging configuration from multiple sources.
"""
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from .base import Config, CoreConfig, ThresholdConfig, ModelConfig, ProfitabilityConfig


def load_league_overrides(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load league-specific configuration overrides from JSON file."""
    if not config_path:
        config_path = Path(__file__).parent / "league_overrides.json"
    
    config_file = Path(config_path)
    if not config_file.exists():
        return {}
    
    with open(config_file, 'r') as f:
        return json.load(f)


def create_config(
    league_name: Optional[str] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
    league_config_path: Optional[str] = None
) -> Config:
    """
    Create configuration with layered overrides.
    
    Args:
        league_name: Name of the league for league-specific overrides
        config_overrides: CLI or programmatic overrides
        league_config_path: Path to league configuration JSON file
        
    Returns:
        Fully configured Config instance
    """
    # Load league overrides
    league_overrides = load_league_overrides(league_config_path)
    
    # Create base config
    config = Config(
        league_name=league_name,
        league_overrides=league_overrides
    )
    
    # Apply CLI/programmatic overrides
    if config_overrides:
        _apply_config_overrides(config, config_overrides)
    
    return config


def _apply_config_overrides(config: Config, overrides: Dict[str, Any]) -> None:
    """Apply configuration overrides to existing config instance."""
    for section_name, section_overrides in overrides.items():
        if hasattr(config, section_name):
            section_config = getattr(config, section_name)
            for key, value in section_overrides.items():
                if hasattr(section_config, key):
                    setattr(section_config, key, value)


def add_config_args(parser: argparse.ArgumentParser) -> None:
    """Add common configuration arguments to CLI parser."""
    # Core settings
    parser.add_argument('--data-dir', type=str, help='Data directory path')
    parser.add_argument('--results-dir', type=str, help='Results output directory')
    parser.add_argument('--random-seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--n-jobs', type=int, help='Number of parallel jobs')
    
    # Threshold settings
    parser.add_argument('--min-accuracy', type=float, help='Minimum pattern accuracy threshold')
    parser.add_argument('--min-matches', type=int, help='Minimum matches for pattern validity')
    parser.add_argument('--confidence-goals', type=float, help='Confidence threshold for goals patterns')
    parser.add_argument('--confidence-corners', type=float, help='Confidence threshold for corners patterns')
    parser.add_argument('--confidence-cards', type=float, help='Confidence threshold for cards patterns')
    
    # Model settings
    parser.add_argument('--use-ensemble', action='store_true', help='Enable ensemble models')
    parser.add_argument('--use-smote', action='store_true', help='Enable SMOTE for imbalanced data')
    parser.add_argument('--cv-folds', type=int, help='Number of cross-validation folds')


def config_from_args(args: argparse.Namespace, league_name: Optional[str] = None) -> Config:
    """Create configuration from parsed CLI arguments."""
    # Build override dictionary from non-None arguments
    overrides = {}
    
    # Core overrides
    core_overrides = {}
    if args.data_dir is not None:
        core_overrides['data_dir'] = args.data_dir
    if args.results_dir is not None:
        core_overrides['results_dir'] = args.results_dir
    if args.random_seed is not None:
        core_overrides['random_seed'] = args.random_seed
    if args.n_jobs is not None:
        core_overrides['n_jobs'] = args.n_jobs
    if core_overrides:
        overrides['core'] = core_overrides
    
    # Threshold overrides
    threshold_overrides = {}
    if args.min_accuracy is not None:
        threshold_overrides['min_accuracy'] = args.min_accuracy
    if args.min_matches is not None:
        threshold_overrides['min_matches'] = args.min_matches
    
    # Confidence thresholds
    confidence_overrides = {}
    if args.confidence_goals is not None:
        confidence_overrides['goals'] = args.confidence_goals
    if args.confidence_corners is not None:
        confidence_overrides['corners'] = args.confidence_corners
    if args.confidence_cards is not None:
        confidence_overrides['cards'] = args.confidence_cards
    if confidence_overrides:
        threshold_overrides['confidence_thresholds'] = confidence_overrides
    
    if threshold_overrides:
        overrides['thresholds'] = threshold_overrides
    
    # Model overrides
    model_overrides = {}
    if args.use_ensemble is not None:
        model_overrides['use_ensemble'] = args.use_ensemble
    if args.use_smote is not None:
        model_overrides['use_smote'] = args.use_smote
    if args.cv_folds is not None:
        model_overrides['cv_folds'] = args.cv_folds
    if model_overrides:
        overrides['models'] = model_overrides
    
    return create_config(
        league_name=league_name,
        config_overrides=overrides
    )
