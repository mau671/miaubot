#!/usr/bin/env python3

import sys
import os

# Import and run the main module
from src.main import main

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


if __name__ == "__main__":
    main()
