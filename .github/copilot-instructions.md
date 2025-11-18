# Football Pattern Betting System v2 - Copilot Instructions

This workspace contains a clean rewrite of the football pattern betting system, designed for clarity, maintainability, and performance.

## Project Structure
- `v2/` - Main v2 codebase with modular architecture
- `config/` - Configuration management with typed dataclasses  
- `patterns/` - Betting pattern registry and definitions
- `models/` - Simple logistic regression trainer (MVP)
- `data/` - Data ingestion and validation
- `eval/` - Backtesting and walk-forward analysis (in progress)

## Development Guidelines
- Follow modular architecture with single-responsibility components
- Use type hints and comprehensive docstrings
- Start simple (logistic regression) before adding complexity
- Prioritize testability and maintainability over performance optimization
- Cache models to avoid redundant training

## Testing Strategy
- Unit tests for pattern functions and configuration loading
- Integration tests with sample datasets
- Performance benchmarks against legacy system

## Configuration
Uses layered configuration: base defaults → league overrides → CLI arguments
All configuration is typed using dataclasses for validation and IDE support.