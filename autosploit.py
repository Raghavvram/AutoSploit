#!/usr/bin/env python3
"""
AutoSploit - Automated Penetration Testing Tool
Modernized for Python 3.12
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autosploit.main import main
from lib.output import error


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        error("user aborted session")
    except Exception as e:
        error(f"unexpected error: {e}")
        sys.exit(1)
