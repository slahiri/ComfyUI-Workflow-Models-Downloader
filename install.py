import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check and install required packages
required_packages = {
    "tavily-python": "tavily",
    "huggingface_hub": "huggingface_hub",
    "requests": "requests",
    "aiohttp": "aiohttp",
    "pyyaml": "yaml",
}

for pip_name, import_name in required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        print(f"[Workflow-Models-Downloader] Installing {pip_name}...")
        install_package(pip_name)
        print(f"[Workflow-Models-Downloader] {pip_name} installed successfully")
