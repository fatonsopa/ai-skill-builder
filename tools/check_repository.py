#!/usr/bin/env python3
"""Use the same impacted/default and explicitly authorized final-test entry point."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_tests import main

if __name__ == "__main__":
    raise SystemExit(main())
