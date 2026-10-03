"""
StackCheck — Web Application Entry Point.
Run with: streamlit run app.py
"""

import sys
from pathlib import Path

# Ensure src is in pythonpath
sys.path.insert(0, str(Path(__file__).parent / "src"))

from stackcheck.web.app import main

if __name__ == "__main__":
    main()
