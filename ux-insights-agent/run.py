#!/usr/bin/env python3
"""
run.py
Command-line interface for the UX Insights Agent.

Usage examples:
  python run.py --task clarity --insights INS-004
  python run.py --task redundancy --insights INS-001 INS-003
  python run.py --task executive --insights INS-001 INS-002
  python run.py --task executive --insights INS-001 --no-save
"""

import argparse
import sys
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent / "agent"))
from orchestrator import run, SKILL_MAP


def main():
    parser = argparse.ArgumentParser(
        description="UX Insights Agent — powered by Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tasks:
  clarity     Review a single insight for clarity and logical integrity
  redundancy  Check multiple insights for overlap or duplication
  executive   Draft C-suite-ready summaries from one or more insights

Examples:
  python run.py --task clarity --insights INS-004
  python run.py --task redundancy --insights INS-001 INS-002 INS-003
  python run.py --task executive --insights INS-001
        """
    )

    parser.add_argument(
        "--task",
        required=True,
        choices=list(SKILL_MAP.keys()),
        help="The type of task to perform"
    )
    parser.add_argument(
        "--insights",
        required=True,
        nargs="+",
        metavar="ID",
        help="One or more insight IDs (e.g. INS-001 INS-002)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print output only, don't save to outputs/"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the Ollama model (default: llama3)"
    )

    args = parser.parse_args()

    # Optional model override
    if args.model:
        import os
        os.environ["OLLAMA_MODEL"] = args.model

    # Validate insight ID format
    for insight_id in args.insights:
        if not insight_id.startswith("INS-"):
            print(f"⚠ Warning: '{insight_id}' doesn't look like a standard ID (expected INS-XXX)")

    try:
        result = run(
            task_type=args.task,
            insight_ids=args.insights,
            save=not args.no_save
        )
        print("=" * 60)
        print(result)
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n✗ File error: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"\n✗ Connection error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Input error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
