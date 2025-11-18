# Football Pattern Betting System v2

A clean, modular rewrite of the football pattern betting and backtesting platform. Built for speed, clarity, and maintainability.

## Architecture Overview

Version 2 addresses the complexity and performance bottlenecks of the legacy system by:

- **Modular Design**: Clear separation of concerns across components
- **Minimal MVP**: Start with logistic regression, add complexity only when justified  
- **Clean Contracts**: Typed interfaces between pattern registry, trainers, and evaluators
- **Efficient Caching**: Avoid retraining unchanged models across runs
- **Transparent Configuration**: Typed dataclasses with layered overrides

## Directory Structure

```
v2/
├── config/          # Configuration management
│   ├── base.py      # Core dataclasses
│   └── loader.py    # Config merging and CLI integration
├── data/            # Data ingestion and validation
│   └── ingest.py    # CSV loading and cleaning
├── features/        # Feature engineering
│   └── builder.py   # Feature construction
├── patterns/        # Betting pattern definitions
│   ├── categories.py # Pattern categories (GOALS/CORNERS/CARDS)
│   └── registry.py  # Pattern registration and management
├── models/          # Model training
│   └── logistic.py  # Simple logistic regression trainer
├── scoring/         # Pattern evaluation
│   ├── metrics.py   # Accuracy, precision, etc.
│   └── profitability.py # Profitability scoring
├── selection/       # Pattern selection logic
│   └── policy.py    # Best pattern selection
├── eval/            # Backtesting and evaluation
│   └── backtest.py  # Main backtesting engine
├── cache/           # Model caching
└── cli.py           # Command-line interface
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements_v2.txt

# Optional: Install in development mode
pip install -e .
```

### Basic Usage

```bash
# List registered patterns
python -m v2.cli patterns

# Run backtest (placeholder - not yet implemented)
python -m v2.cli backtest --league Romania --start-date 2023-01-01 --end-date 2023-12-31

# Run walk-forward analysis (placeholder - not yet implemented)  
python -m v2.cli walkforward --league Romania --start-date 2023-01-01 --end-date 2023-12-31
```

## Current Implementation Status

✅ **Completed**:
- Core configuration system with typed dataclasses
- Pattern registry with sample patterns (goals, corners, cards)
- Data ingestion with validation and cleaning
- Simple logistic regression trainer
- CLI interface structure

🚧 **In Progress**:
- Feature engineering module
- Metrics calculation and profitability scoring
- Pattern selection policies
- Backtesting engine
- Model caching

📋 **Planned**:
- Walk-forward evaluation
- Enhanced ensemble models (optional)
- Dynamic threshold learning
- Performance optimizations

## Configuration

The system uses a layered configuration approach:

1. **Base defaults** in `config/base.py`
2. **League-specific overrides** via JSON files
3. **CLI arguments** for runtime customization

Example configuration:

```python
from v2.config.loader import create_config

config = create_config(
    league_name="Romania",
    config_overrides={
        'thresholds': {
            'min_accuracy': 0.60,
            'confidence_thresholds': {
                'goals': 0.70
            }
        }
    }
)
```

## Pattern Definition

Define new betting patterns by registering them with the pattern registry:

```python
from v2.patterns.registry import register_pattern
from v2.patterns.categories import PatternCategory

def my_custom_pattern(row):
    """Custom pattern logic."""
    return row['FTHG'] > 2 and row['HC'] > 5

register_pattern(
    name="home_goals_and_corners",
    category=PatternCategory.GOALS,
    label_fn=my_custom_pattern,
    default_threshold=0.65,
    min_matches=25,
    description="Home team scores 2+ goals and gets 5+ corners"
)
```

## Design Principles

### 1. Start Simple
- Begin with logistic regression only
- Add ensemble methods only when performance gains are demonstrated
- Defer complex features (stacking, calibration) to later phases

### 2. Explicit Over Implicit
- No global state or hidden dependencies  
- Clear function signatures with typed parameters
- Transparent profitability scoring with configurable weights

### 3. Fast Iteration
- Model caching to avoid redundant training
- Minimal feature set initially, expand based on needs
- Parallel training where beneficial

### 4. Testing & Validation
- Unit tests for pattern functions and metrics
- Integration tests with mock datasets
- Performance regression tests

## Migration from Legacy System

The v2 system is designed to run side-by-side with the legacy codebase:

1. Keep existing `src/` directory intact
2. Build v2 incrementally in parallel
3. Compare results on identical datasets
4. Migrate patterns and adjust thresholds as needed

## Development Roadmap

### Phase 1: MVP (Current)
- [x] Core infrastructure and configuration
- [x] Pattern registry with sample patterns
- [x] Simple logistic trainer
- [ ] Feature engineering
- [ ] Basic backtesting

### Phase 2: Core Features
- [ ] Metrics and profitability scoring
- [ ] Pattern selection policies
- [ ] Walk-forward evaluation
- [ ] Model caching

### Phase 3: Enhancements
- [ ] Ensemble models (if justified)
- [ ] Dynamic threshold learning
- [ ] Performance optimizations
- [ ] Advanced pattern retirement logic

## Contributing

When adding new components:

1. Follow the existing modular structure
2. Add type hints and docstrings
3. Include unit tests for new functionality
4. Update this README with any architectural changes

## Performance Targets

- **Training**: < 10 seconds per team/pattern combination
- **Backtesting**: < 5 minutes for full season analysis
- **Memory**: < 2GB peak usage for typical league datasets
- **Accuracy**: Match or exceed legacy system performance

---

## Legacy System Comparison

| Aspect | Legacy | v2 |
|--------|--------|-----|
| Architecture | Monolithic `main.py` | Modular components |
| Configuration | Environment variables | Typed dataclasses |
| Models | Ensemble + stacking | Logistic regression MVP |
| State Management | Global variables | Explicit parameters |
| Testing | Limited | Comprehensive test suite |
| Performance | Heavy ensemble training | Fast minimal models |

The v2 system prioritizes maintainability and iteration speed while preserving the core betting logic and evaluation methodology of the original system.