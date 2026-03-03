#!/usr/bin/env python3
"""
Command-line interface for the LLM-as-a-Judge Evaluation Framework.

Usage:
    python cli.py --transcript transcript.txt --output structured_output.json --results results.json
"""

import argparse
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation_engine import EvaluationEngine


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="LLM-as-a-Judge Evaluation Framework for Sales Call Transcripts"
    )
    
    parser.add_argument(
        "--transcript", "-t",
        type=str,
        required=True,
        help="Path to the transcript text file"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to the structured output JSON file"
    )
    
    parser.add_argument(
        "--results", "-r",
        type=str,
        required=True,
        help="Path to save the evaluation results JSON file"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-oss-120b",
        help="LLM model to use for evaluation (default: openai/gpt-oss-120b)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for LLM generation (default: 0.0)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def load_transcript(file_path: str) -> str:
    """Load transcript from text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        sys.exit(1)


def load_structured_output(file_path: str) -> dict:
    """Load structured output from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Structured output file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing structured output JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading structured output file: {e}")
        sys.exit(1)


def save_results(results: dict, file_path: str):
    """Save evaluation results to JSON file."""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Evaluation results saved to: {file_path}")
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    args = parse_arguments()
    
    # Set up logging if verbose
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    # Validate API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not set.")
        print("Please set your Groq API key:")
        print("export GROQ_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Load inputs
    print("Loading transcript and structured output...")
    transcript = load_transcript(args.transcript)
    structured_output = load_structured_output(args.output)
    
    # Initialize evaluation engine
    print("Initializing evaluation engine...")
    model_config = {
        "model_name": args.model,
        "temperature": args.temperature
    }
    
    engine = EvaluationEngine(model_config)
    
    # Run evaluation
    print("Running evaluation...")
    try:
        results = engine.evaluate_call(transcript, structured_output)
        
        # Save results
        save_results(results, args.results)
        
        # Print summary
        print("\n=== EVALUATION SUMMARY ===")
        print(f"Call Type: {results['call_type_validation']['predicted_call_type']}")
        print(f"Sub Type: {results['call_type_validation']['predicted_sub_type']}")
        print(f"Call Type Confidence: {results['call_type_validation']['confidence']}")
        print(f"Schema Validation: {'PASSED' if results['schema_validation']['schema_passed'] else 'FAILED'}")
        print(f"Overall Score: {results['overall_score']:.2f}/5.0")
        
        if results['schema_validation']['missing_fields']:
            print(f"Missing Fields: {len(results['schema_validation']['missing_fields'])}")
        
        if results['segment_evaluations']:
            print(f"Segments Evaluated: {len(results['segment_evaluations'])}")
            for segment in results['segment_evaluations']:
                print(f"  - {segment['segment_name']}: {segment['weighted_score']:.2f}")
        
        print("\nEvaluation completed successfully!")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()