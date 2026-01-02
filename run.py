"""
Entry point for the Educational Data Chatbot.

Run this file to start the Streamlit application.
Usage: streamlit run run.py
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main app
from app import main

if __name__ == "__main__":
    main()


