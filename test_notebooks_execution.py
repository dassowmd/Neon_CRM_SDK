#!/usr/bin/env python3
"""Execute Jupyter notebooks to test they run without errors.

This script actually executes notebooks to verify they work correctly.
It's a regression test to ensure notebooks still function after code changes.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def check_notebook_for_errors(notebook_path: Path) -> Tuple[bool, List[str]]:
    """Check if notebook outputs contain any errors.

    Returns:
        Tuple of (success, list of error messages)
    """
    try:
        with open(notebook_path) as f:
            nb = json.load(f)

        errors = []

        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") == "code":
                outputs = cell.get("outputs", [])
                for output in outputs:
                    # Check for error/traceback outputs
                    if output.get("output_type") == "error":
                        ename = output.get("ename", "Error")
                        evalue = output.get("evalue", "Unknown error")
                        errors.append(f"Cell {i}: {ename}: {evalue}")

                    # Check for stream outputs with error indicators
                    elif output.get("output_type") == "stream":
                        text = "".join(output.get("text", []))
                        # Only check for actual Python tracebacks, not user-friendly error messages
                        if "Traceback (most recent call last)" in text:
                            errors.append(
                                f"Cell {i}: Traceback in output: {text[:200]}..."
                            )

        if errors:
            return False, errors
        return True, ["No errors found in cell outputs"]

    except Exception as e:
        return False, [f"Error checking notebook outputs: {e}"]


def execute_notebook(notebook_path: Path) -> Tuple[bool, str]:
    """Execute a notebook and check for errors.

    Returns:
        Tuple of (success, message)
    """
    try:
        # Use jupyter nbconvert to execute the notebook
        # Allow errors to continue execution so we can check outputs
        subprocess.run(
            [
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=300",  # 5 minute timeout per cell
                "--ExecutePreprocessor.kernel_name=python3",
                "--ExecutePreprocessor.allow_errors=True",  # Continue on errors
                str(notebook_path),
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute total timeout
            env={
                **subprocess.os.environ,
                "MPLBACKEND": "Agg",
            },  # Use non-interactive matplotlib backend
        )

        # Regardless of return code, check the notebook outputs for actual errors
        # (allow_errors=True means it can succeed even with cell errors)
        success, messages = check_notebook_for_errors(notebook_path)

        if success:
            return True, "Executed successfully - no errors in outputs"
        else:
            # Return first few error messages
            error_summary = "; ".join(messages[:3])
            if len(messages) > 3:
                error_summary += f" (and {len(messages) - 3} more errors)"
            return False, error_summary

    except subprocess.TimeoutExpired:
        return False, "Execution timeout (>10 minutes)"
    except Exception as e:
        return False, f"Execution error: {str(e)}"


def test_notebook(notebook_path: Path, dry_run: bool = False) -> bool:
    """Test a single notebook.

    Args:
        notebook_path: Path to the notebook
        dry_run: If True, only validate structure without executing

    Returns:
        True if passed, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Testing: {notebook_path}")
    print("=" * 70)

    # First check if it's valid JSON
    try:
        with open(notebook_path) as f:
            json.load(f)
        print("✓ Valid JSON structure")
    except Exception as e:
        print(f"✗ Invalid JSON: {e}")
        return False

    if dry_run:
        print("ℹ Dry run - skipping execution")
        return True

    # Execute the notebook
    print("⏳ Executing notebook (this may take a few minutes)...")
    success, message = execute_notebook(notebook_path)

    if success:
        print(f"✓ {message}")
        return True
    else:
        print(f"✗ Execution failed:")
        print(f"  {message}")
        return False


def main():
    """Run notebook execution tests."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Execute notebooks as regression tests"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate structure without executing notebooks",
    )
    parser.add_argument(
        "--pattern",
        default="examples/*.ipynb,analysis/*.ipynb",
        help="Comma-separated glob patterns for notebooks to test (default: examples/*.ipynb,analysis/*.ipynb)",
    )
    parser.add_argument(
        "--skip",
        default="",
        help="Comma-separated list of notebook names to skip (e.g., 'basic_usage.ipynb,donor_lifecycle.ipynb')",
    )

    args = parser.parse_args()

    print("Jupyter Notebook Execution Test")
    print("=" * 70)

    if args.dry_run:
        print("🔍 DRY RUN MODE - Structure validation only")
        print()

    # Find all notebooks matching patterns
    notebooks = []
    patterns = [p.strip() for p in args.pattern.split(",")]
    skip_names = {s.strip() for s in args.skip.split(",") if s.strip()}

    for pattern in patterns:
        found = list(Path(".").glob(pattern))
        # Filter out skipped notebooks
        found = [nb for nb in found if nb.name not in skip_names]
        notebooks.extend(found)

    if not notebooks:
        print("❌ No notebooks found!")
        print(f"Patterns: {patterns}")
        return 1

    # Filter out skipped notebooks
    print(f"Found {len(notebooks)} notebook(s) to test")
    if skip_names:
        print(f"Skipping: {', '.join(skip_names)}")
    print()

    results = {}
    for notebook in sorted(notebooks):
        passed = test_notebook(notebook, dry_run=args.dry_run)
        results[notebook] = passed

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    for notebook, passed in sorted(results.items()):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {notebook}")

    print(f"\nTotal: {passed_count}/{total_count} notebooks passed")

    if passed_count == total_count:
        print("\n🎉 All notebooks passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} notebook(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
