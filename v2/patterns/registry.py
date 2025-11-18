"""
Pattern registry for football betting patterns.
Provides clean interface for pattern registration and retrieval.
"""
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from .categories import PatternCategory


@dataclass
class Pattern:
    """Represents a betting pattern with metadata."""
    name: str
    category: PatternCategory
    label_fn: Callable[[pd.Series], bool]
    default_threshold: float
    min_matches: int
    description: str = ""
    
    def __post_init__(self):
        """Validate pattern after creation."""
        if not callable(self.label_fn):
            raise ValueError(f"Pattern '{self.name}': label_fn must be callable")
        if not (0.0 <= self.default_threshold <= 1.0):
            raise ValueError(f"Pattern '{self.name}': threshold must be between 0 and 1")
        if self.min_matches < 1:
            raise ValueError(f"Pattern '{self.name}': min_matches must be >= 1")


class PatternRegistry:
    """Registry for managing betting patterns."""
    
    def __init__(self):
        """Initialize empty pattern registry."""
        self._patterns: Dict[str, Pattern] = {}
    
    def register(self, pattern: Pattern) -> None:
        """
        Register a new pattern.
        
        Args:
            pattern: Pattern instance to register
            
        Raises:
            ValueError: If pattern name already exists
        """
        if pattern.name in self._patterns:
            raise ValueError(f"Pattern '{pattern.name}' is already registered")
        
        self._patterns[pattern.name] = pattern
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """Get pattern by name."""
        return self._patterns.get(name)
    
    def get_patterns_by_category(self, category: PatternCategory) -> List[Pattern]:
        """Get all patterns for a specific category."""
        return [p for p in self._patterns.values() if p.category == category]
    
    def list_patterns(self) -> List[str]:
        """Get list of all registered pattern names."""
        return list(self._patterns.keys())
    
    def get_all_patterns(self) -> List[Pattern]:
        """Get all registered patterns."""
        return list(self._patterns.values())
    
    def clear(self) -> None:
        """Clear all registered patterns."""
        self._patterns.clear()
    
    def validate_pattern(self, pattern_name: str, sample_row: pd.Series) -> bool:
        """
        Validate a pattern by testing it on a sample row.
        
        Args:
            pattern_name: Name of the pattern to validate
            sample_row: Sample match row to test
            
        Returns:
            True if pattern executes without error
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False
        
        try:
            result = pattern.label_fn(sample_row)
            return isinstance(result, bool)
        except Exception:
            return False


# Global registry instance
_global_registry = PatternRegistry()


def register_pattern(
    name: str,
    category: PatternCategory,
    label_fn: Callable[[pd.Series], bool],
    default_threshold: float = 0.65,
    min_matches: int = 20,
    description: str = ""
) -> None:
    """
    Register a pattern in the global registry.
    
    Args:
        name: Unique pattern name
        category: Pattern category
        label_fn: Function that takes a match row and returns boolean
        default_threshold: Default confidence threshold
        min_matches: Minimum matches required for validity
        description: Optional pattern description
    """
    pattern = Pattern(
        name=name,
        category=category,
        label_fn=label_fn,
        default_threshold=default_threshold,
        min_matches=min_matches,
        description=description
    )
    _global_registry.register(pattern)


def get_pattern_registry() -> PatternRegistry:
    """Get the global pattern registry."""
    return _global_registry


def list_registered_patterns() -> List[str]:
    """Get list of all registered pattern names."""
    return _global_registry.list_patterns()


def clear_patterns() -> None:
    """Clear all registered patterns."""
    _global_registry.clear()


# Example pattern definitions
def _home_over_1_5_goals(row: pd.Series) -> bool:
    """Pattern: Home team scores over 1.5 goals."""
    return row['FTHG'] > 1.5


def _total_over_2_5_goals(row: pd.Series) -> bool:
    """Pattern: Total goals over 2.5."""
    return (row['FTHG'] + row['FTAG']) > 2.5


def _home_over_4_corners(row: pd.Series) -> bool:
    """Pattern: Home team gets over 4 corners."""
    return row.get('HC', 0) > 4


def _total_over_8_corners(row: pd.Series) -> bool:
    """Pattern: Total corners over 8."""
    home_corners = row.get('HC', 0)
    away_corners = row.get('AC', 0)
    return (home_corners + away_corners) > 8


def _home_over_1_cards(row: pd.Series) -> bool:
    """Pattern: Home team gets over 1 card."""
    home_yellows = row.get('HY', 0)
    home_reds = row.get('HR', 0)
    return (home_yellows + home_reds) > 1


# Register example patterns
register_pattern(
    name="home_over_1_5_goals",
    category=PatternCategory.GOALS,
    label_fn=_home_over_1_5_goals,
    default_threshold=0.65,
    min_matches=20,
    description="Home team scores over 1.5 goals"
)

register_pattern(
    name="total_over_2_5_goals", 
    category=PatternCategory.GOALS,
    label_fn=_total_over_2_5_goals,
    default_threshold=0.65,
    min_matches=20,
    description="Total goals over 2.5"
)

register_pattern(
    name="home_over_4_corners",
    category=PatternCategory.CORNERS,
    label_fn=_home_over_4_corners,
    default_threshold=0.60,
    min_matches=15,
    description="Home team gets over 4 corners"
)

register_pattern(
    name="total_over_8_corners",
    category=PatternCategory.CORNERS,
    label_fn=_total_over_8_corners,
    default_threshold=0.60,
    min_matches=15,
    description="Total corners over 8"
)

register_pattern(
    name="home_over_1_cards",
    category=PatternCategory.CARDS,
    label_fn=_home_over_1_cards,
    default_threshold=0.70,
    min_matches=25,
    description="Home team gets over 1 card"
)
