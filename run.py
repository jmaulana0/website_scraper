#!/usr/bin/env python3
"""
Runner script for the DNB Selenium scraper
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from selenium_scraper import main
    main()
