"""
Pattern categories and constants for betting patterns.
"""
from enum import Enum


class PatternCategory(Enum):
    """Categories for betting patterns."""
    GOALS = "goals"
    CORNERS = "corners"
    CARDS = "cards"


# Default confidence thresholds per category
DEFAULT_CONFIDENCE_THRESHOLDS = {
    PatternCategory.GOALS: 0.65,
    PatternCategory.CORNERS: 0.60,
    PatternCategory.CARDS: 0.70
}


# Minimum matches required per category
DEFAULT_MIN_MATCHES = {
    PatternCategory.GOALS: 20,
    PatternCategory.CORNERS: 15,
    PatternCategory.CARDS: 25
}
