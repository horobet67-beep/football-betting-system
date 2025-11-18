"""
Command-line interface for the v2 football betting system.
Provides entry points for backtesting and walk-forward analysis.
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Add v2 to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import create_config, add_config_args, config_from_args


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_base_parser() -> argparse.ArgumentParser:
    """Create base argument parser with common options."""
    parser = argparse.ArgumentParser(
        description="Football Pattern Betting System v2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    parser.add_argument(
        '--league',
        required=True,
        help='League name (e.g., "Romania", "England")'
    )
    
    return parser


def create_backtest_parser() -> argparse.ArgumentParser:
    """Create parser for backtest command."""
    parser = create_base_parser()
    parser.prog = 'python -m v2.cli backtest'
    
    parser.add_argument(
        '--start-date',
        required=True,
        help='Backtest start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        required=True,
        help='Backtest end date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Output directory for results'
    )
    
    # Add common config arguments
    add_config_args(parser)
    
    return parser


def create_walkforward_parser() -> argparse.ArgumentParser:
    """Create parser for walk-forward command."""
    parser = create_base_parser()
    parser.prog = 'python -m v2.cli walkforward'
    
    parser.add_argument(
        '--start-date',
        required=True,
        help='Walk-forward start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        required=True,
        help='Walk-forward end date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--fold-days',
        type=int,
        default=7,
        help='Days between fold start dates'
    )
    
    parser.add_argument(
        '--test-days',
        type=int,
        default=7,
        help='Number of test days per fold'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Output directory for results'
    )
    
    # Add common config arguments
    add_config_args(parser)
    
    return parser


def cmd_backtest(args: argparse.Namespace) -> int:
    """Execute backtest command."""
    try:
        # Setup logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        # Create configuration
        config = config_from_args(args, league_name=args.league)
        
        logger.info(f"Starting backtest for league '{args.league}'")
        logger.info(f"Date range: {args.start_date} to {args.end_date}")
        
        # Import and run backtest
        from eval.backtest import run_simple_backtest, print_backtest_results
        
        results = run_simple_backtest(
            league_name=args.league,
            start_date=args.start_date,
            end_date=args.end_date,
            config=config.core.__dict__  # Convert to dict
        )
        
        # Print results
        print_backtest_results(results)
        
        # Save results if output directory specified
        if args.output_dir:
            import os
            import json
            from pathlib import Path
            
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            results_dict = {
                'league': results.league,
                'start_date': results.start_date,
                'end_date': results.end_date,
                'total_matches': results.total_matches,
                'total_bets': results.total_bets,
                'winning_bets': results.winning_bets,
                'total_stake': results.total_stake,
                'total_return': results.total_return,
                'win_rate': results.win_rate,
                'roi': results.roi,
                'pattern_stats': results.pattern_stats
            }
            
            results_file = output_path / f"backtest_{args.league}_{args.start_date}_{args.end_date}.json"
            with open(results_file, 'w') as f:
                json.dump(results_dict, f, indent=2)
            
            logger.info(f"Results saved to {results_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_walkforward(args: argparse.Namespace) -> int:
    """Execute walk-forward command."""
    try:
        # Setup logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        # Create configuration
        config = config_from_args(args, league_name=args.league)
        
        logger.info(f"Starting walk-forward for league '{args.league}'")
        logger.info(f"Date range: {args.start_date} to {args.end_date}")
        logger.info(f"Fold configuration: {args.fold_days} day stride, {args.test_days} test days")
        
        # TODO: Import and run walk-forward
        # from eval.walkforward import run_walkforward
        # results = run_walkforward(
        #     league=args.league,
        #     start_date=args.start_date,
        #     end_date=args.end_date,
        #     fold_days=args.fold_days,
        #     test_days=args.test_days,
        #     config=config,
        #     output_dir=args.output_dir
        # )
        
        logger.info("Walk-forward functionality not yet implemented")
        logger.info(f"Configuration: {config}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Walk-forward failed: {e}")
        return 1


def cmd_enhanced_backtest(args: argparse.Namespace) -> int:
    """Execute enhanced backtest command."""
    try:
        # Setup logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        # Create configuration
        config = config_from_args(args, league_name=args.league)
        
        # Add enhanced backtest specific config
        backtest_config = {
            'unit_stake': args.unit_stake,
            'min_confidence': args.min_confidence,
            'max_bets_per_day': args.max_bets_per_day
        }
        
        logger.info(f"Starting enhanced backtest for league '{args.league}'")
        logger.info(f"Date range: {args.start_date} to {args.end_date}")
        logger.info(f"Config: {backtest_config}")
        
        # Import and run enhanced backtest
        from eval.enhanced_backtest import run_enhanced_backtest, print_enhanced_results, save_enhanced_results
        
        results = run_enhanced_backtest(
            league_name=args.league,
            start_date=args.start_date,
            end_date=args.end_date,
            config=backtest_config
        )
        
        # Print results
        print_enhanced_results(results)
        
        # Save results if output directory specified
        if args.output_dir:
            results_file = save_enhanced_results(results, args.output_dir)
            logger.info(f"Enhanced results saved to {results_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Enhanced backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_patterns(args: argparse.Namespace) -> int:
    """List registered patterns."""
    try:
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        # Import Romanian patterns to ensure they're registered
        import patterns.romanian_patterns
        
        from patterns.registry import get_pattern_registry
        
        registry = get_pattern_registry()
        patterns = registry.get_all_patterns()
        
        print(f"\n{len(patterns)} registered patterns:")
        print("-" * 60)
        
        for pattern in patterns:
            print(f"{pattern.name:25} {pattern.category.value:10} {pattern.default_threshold:.2f} {pattern.min_matches:3}")
        
        print("-" * 60)
        print(f"{'Name':<25} {'Category':<10} {'Threshold':<9} {'MinMatches'}")
        
        return 0
        
    except Exception as e:
        print(f"Error listing patterns: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    # Create main parser with subcommands
    parser = argparse.ArgumentParser(
        description="Football Pattern Betting System v2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add subcommands
    backtest_parser = create_backtest_parser()
    subparsers.add_parser('backtest', parents=[backtest_parser], add_help=False)
    
    walkforward_parser = create_walkforward_parser()
    subparsers.add_parser('walkforward', parents=[walkforward_parser], add_help=False)
    
    # Patterns command
    patterns_parser = subparsers.add_parser('patterns', help='List registered patterns')
    patterns_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    # Enhanced backtest command
    enhanced_parser = create_base_parser()
    enhanced_parser.prog = 'python -m v2.cli enhanced-backtest'
    enhanced_parser.add_argument('--start-date', required=True, help='Backtest start date (YYYY-MM-DD)')
    enhanced_parser.add_argument('--end-date', required=True, help='Backtest end date (YYYY-MM-DD)')
    enhanced_parser.add_argument('--output-dir', help='Output directory for results')
    enhanced_parser.add_argument('--unit-stake', type=float, default=1.0, help='Unit stake per bet')
    enhanced_parser.add_argument('--min-confidence', type=float, default=0.65, help='Minimum confidence threshold')
    enhanced_parser.add_argument('--max-bets-per-day', type=int, default=5, help='Maximum bets per day')
    add_config_args(enhanced_parser)
    subparsers.add_parser('enhanced-backtest', parents=[enhanced_parser], add_help=False)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == 'backtest':
        return cmd_backtest(args)
    elif args.command == 'enhanced-backtest':
        return cmd_enhanced_backtest(args)
    elif args.command == 'walkforward':
        return cmd_walkforward(args)
    elif args.command == 'patterns':
        return cmd_patterns(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
