import os
import sys

# Adjust path to the root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Import and execute the real render_start
import render_start
