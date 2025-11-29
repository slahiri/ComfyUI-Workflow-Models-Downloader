"""
ComfyUI Workflow Models Downloader
Scans the active workflow for missing models and provides a UI to download them from HuggingFace.

Features:
- Scans active workflow JSON for model references
- Identifies missing models and their target directories
- Shows model information in a modal dialog
- Downloads missing models from HuggingFace with progress tracking
"""

import subprocess
import sys
import importlib.metadata
import os
from pathlib import Path

# Check and install required packages on startup
def check_requirements():
    """Check if all required packages are installed, install if missing"""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        return True

    # Map pip package names to import names
    pip_to_import = {
        "tavily-python": "tavily",
        "huggingface_hub": "huggingface_hub",
        "huggingface-hub": "huggingface_hub",
        "pyyaml": "yaml",
    }

    missing = []

    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Get package name without version specifiers
            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('<')[0].split('>')[0].strip()
            import_name = pip_to_import.get(pkg_name, pkg_name.replace('-', '_'))

            # Check if installed using importlib.metadata
            try:
                importlib.metadata.version(pkg_name)
            except importlib.metadata.PackageNotFoundError:
                # Also try with underscores/hyphens swapped
                alt_name = pkg_name.replace('-', '_') if '-' in pkg_name else pkg_name.replace('_', '-')
                try:
                    importlib.metadata.version(alt_name)
                except importlib.metadata.PackageNotFoundError:
                    missing.append(pkg_name)

    if missing:
        print(f"[Workflow-Models-Downloader] Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "-q"],
                stdout=subprocess.DEVNULL
            )
            print(f"[Workflow-Models-Downloader] Packages installed successfully")
        except Exception as e:
            print(f"[Workflow-Models-Downloader] Failed to install packages: {e}")
            return False

    return True

# Run check before any other imports
check_requirements()

# Add the extension directory to path for imports
extension_path = os.path.dirname(__file__)
if extension_path not in sys.path:
    sys.path.insert(0, extension_path)

# Import and register the server routes
from . import server

# Initialize database and run migrations if needed
try:
    from . import storage
    storage.init_storage()
except Exception as e:
    import logging
    logging.warning(f"[WMD] Storage initialization skipped: {e}")

WEB_DIRECTORY = "js"
NODE_CLASS_MAPPINGS = {}
__all__ = ['NODE_CLASS_MAPPINGS', 'WEB_DIRECTORY']
