import sys
import os

# Add the backend directory to the path using absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, '..', 'backend')
sys.path.append(backend_path)

from app import app as application

# This is the entry point for Vercel
app = application
