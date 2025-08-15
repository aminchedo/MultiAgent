"""
Vercel serverless function entry point for the Multi-Agent Code Generation System.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the Vercel-specific FastAPI app
from api.vercel_app import app

# Export the app for Vercel
handler = app
