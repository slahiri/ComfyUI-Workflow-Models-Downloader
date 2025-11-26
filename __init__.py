"""
ComfyUI Workflow Models Downloader
Scans the active workflow for missing models and provides a UI to download them from HuggingFace.

Features:
- Scans active workflow JSON for model references
- Identifies missing models and their target directories
- Shows model information in a modal dialog
- Downloads missing models from HuggingFace with progress tracking
"""

import os
import sys

# Add the extension directory to path for imports
extension_path = os.path.dirname(__file__)
if extension_path not in sys.path:
    sys.path.insert(0, extension_path)

# Import and register the server routes
from . import server

WEB_DIRECTORY = "js"
NODE_CLASS_MAPPINGS = {}
__all__ = ['NODE_CLASS_MAPPINGS', 'WEB_DIRECTORY']
