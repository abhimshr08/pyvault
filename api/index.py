import sys
import os

# Add src directory to system path to import pyvault
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pyvault.web import app
