# Architecture Document

This document captures the existing system architecture of the football pattern betting/backtest platform and proposes a simplified Version 2 (v2) design starting from zero. It highlights bottlenecks, implicit behaviors, and redesign principles for maintainability, speed, and clarity.

## High-Level System Goals
- Ingest historical match CSV data per league.
- Engineer features (rolling/team/referee/trend adjustments).
- Define pattern functions (events like corners, goals, cards conditions).
- Train predictive models per team × pattern (classification: event occurs or not).
- Score patterns (accuracy, precision, coverage, event rate → profitability_score).
- Select highest-confidence pattern prediction per match (HOME vs AWAY) and simulate bets.
- Walk-forward evaluation (time-sliced folds) + recent-days backtest.
- Persist results for review and incremental pattern threshold learning.

## v2 System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Ingest   │───▶│ Feature Builder │───▶│ Pattern Registry│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │    Caching      │    │  Model Trainer  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Evaluator     │◀───│   Scorer        │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Selector      │
                       └─────────────────┘
```

### Data Flow

1. **Ingestion**: Load league CSV files with validation and cleaning
2. **Features**: Build rolling statistics and team/referee features  
3. **Patterns**: Apply pattern label functions to generate target variables
4. **Training**: Fit models per team/pattern combination with caching
5. **Scoring**: Calculate metrics and profitability scores
6. **Selection**: Choose best patterns per match using confidence thresholds
7. **Evaluation**: Run backtests and walk-forward analysis

### Configuration System

Three-layer configuration with clear precedence:

```
Base Defaults (base.py)
    ↓ (overridden by)
League Config (JSON)
    ↓ (overridden by) 
CLI Arguments
    ↓
Final Config
```

### Pattern System

Patterns are first-class objects with metadata:

```python
@dataclass
class Pattern:
    name: str                           # Unique identifier
    category: PatternCategory           # GOALS/CORNERS/CARDS
    label_fn: Callable[[pd.Series], bool] # Pattern logic
    default_threshold: float            # Confidence threshold
    min_matches: int                    # Validation requirement
```

### Model Training

Simple, fast trainer with extensibility:

```python
class SimpleLogisticTrainer:
    def fit(self, X, y, pattern_name, team_name) -> Self
    def predict_proba(self, X) -> np.ndarray
    def get_feature_importance() -> pd.Series
```

## Design Decisions

### 1. Start with Minimal Models
- **Decision**: Begin with logistic regression only
- **Rationale**: Faster iteration, easier debugging, sufficient baseline
- **Future**: Add ensembles only if demonstrated improvement

### 2. Explicit Configuration
- **Decision**: Typed dataclasses instead of environment variables
- **Rationale**: Better IDE support, validation, testability
- **Implementation**: Layered overrides with clear precedence

### 3. Pattern Registry
- **Decision**: Centralized pattern management with metadata
- **Rationale**: Easy to add/remove patterns, validate implementations
- **Benefits**: Supports pattern retirement, A/B testing

### 4. Caching Strategy
- **Decision**: Cache trained models by (league, team, pattern, features)
- **Rationale**: Avoid expensive retraining across runs
- **Implementation**: Hash-based cache keys with version tracking

### 5. Modular Architecture  
- **Decision**: Single-responsibility modules with clean interfaces
- **Rationale**: Testability, maintainability, parallel development
- **Trade-off**: More files vs. monolithic simplicity

## Performance Optimizations

### Current Bottlenecks (Legacy System)
1. **Per-team training**: 20 teams × 50 patterns × 5 models = 5,000 fits
2. **Stacking overhead**: Cross-validation for meta-models
3. **Feature explosion**: 200+ features with limited selection
4. **No caching**: Recompute everything each run

### v2 Improvements
1. **Simplified models**: Logistic only reduces training by 80%
2. **Intelligent caching**: Reuse models when inputs unchanged
3. **Feature focus**: Start with 20-30 core features
4. **Lazy evaluation**: Compute features/models only when needed

## Migration Strategy

### Phase 1: Infrastructure
- ✅ Configuration system
- ✅ Pattern registry
- ✅ Data ingestion
- ✅ Simple trainer
- 🚧 Feature builder

### Phase 2: Core Engine
- 📋 Metrics calculation
- 📋 Profitability scoring  
- 📋 Pattern selection
- 📋 Backtesting engine

### Phase 3: Advanced Features
- 📋 Walk-forward evaluation
- 📋 Model caching
- 📋 Ensemble models (if justified)
- 📋 Dynamic thresholds

### Phase 4: Production
- 📋 Performance tuning
- 📋 Monitoring and logging
- 📋 Error handling
- 📋 Documentation

## Success Criteria

### Functional Requirements
- ✅ Match legacy system accuracy on test datasets
- 📋 Support all existing pattern types
- 📋 Maintain walk-forward evaluation capability
- 📋 Preserve profitability scoring methodology

### Non-Functional Requirements  
- **Performance**: 5x faster than legacy system
- **Maintainability**: 80% test coverage, clear module boundaries
- **Reliability**: Graceful handling of edge cases
- **Extensibility**: Easy to add new patterns and models

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance regression | High | Medium | Benchmark against legacy system |
| Feature compatibility | Medium | Low | Systematic validation on known datasets |
| Model underfitting | Medium | Medium | Baseline with proven logistic features |
| Configuration complexity | Low | Medium | Comprehensive documentation and examples |

## Testing Strategy

### Unit Tests
- Pattern label functions (edge cases, expected outputs)
- Configuration merging logic
- Model training edge cases (insufficient data, constant features)
- Metrics calculations (precision/recall corner cases)

### Integration Tests
- End-to-end backtest on sample dataset
- Configuration loading from files
- Pattern registry with real match data

### Performance Tests
- Training time benchmarks
- Memory usage profiling
- Scalability tests (large datasets)

This architecture document will be updated as the v2 system evolves and requirements are refined based on real-world usage and performance characteristics.