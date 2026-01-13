#!/usr/bin/env python3
"""Test runner script for EXIF-Clone project"""

import subprocess
import sys


def run_tests(test_type="all", verbose=False):
    """
    Run tests based on test type

    Args:
        test_type: "all", "unit", "integration", or specific test file
        verbose: Enable verbose output
    """
    cmd = ["pytest"]

    if verbose:
        cmd.append("-vv")

    if test_type == "unit":
        cmd.append("__tests__/unit/")
    elif test_type == "integration":
        cmd.append("__tests__/integration/")
    elif test_type == "all":
        cmd.append("__tests__/")
    else:
        cmd.append(test_type)

    # Add coverage report
    cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"

    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    exit_code = run_tests(test_type, verbose)
    sys.exit(exit_code)
