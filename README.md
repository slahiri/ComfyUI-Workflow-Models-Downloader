# ComfyUI Workflow Models Downloader

[![CircleCI](https://circleci.com/gh/slahiri/ComfyUI-Workflow-Models-Downloader/tree/main.svg?style=shield)](https://circleci.com/gh/slahiri/ComfyUI-Workflow-Models-Downloader?branch=main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/slahiri/ComfyUI-Workflow-Models-Downloader.svg)](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/slahiri/ComfyUI-Workflow-Models-Downloader.svg)](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues)

A ComfyUI extension that automatically detects models in your workflow and helps download missing ones from HuggingFace and CivitAI.

![Screenshot](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/raw/main/screenshot.png)

## Features

- **Auto-detect models** - Scans your active workflow for all model references
- **Smart URL detection** - Finds download URLs from multiple sources:
  - Workflow metadata (embedded URLs)
  - Popular models registry (curated list)
  - ComfyUI Manager model list
  - HuggingFace API search
  - CivitAI API search
- **One-click download** - Download missing models directly from the UI
- **Manual URL support** - Paste direct download URLs for models not found automatically
- **Background downloads** - Downloads continue even when modal is closed
- **Progress tracking** - Real-time download progress with notifications
- **Directory selection** - Choose target directory for each model

## Installation

### Via ComfyUI Manager (Recommended)
Search for "Workflow Models Downloader" in ComfyUI Manager and click Install.

### Manual Installation
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader.git
pip install -r ComfyUI-Workflow-Models-Downloader/requirements.txt
```

Restart ComfyUI after installation.

## Usage

1. Open any workflow in ComfyUI
2. Click **"Missing Models"** button in the top menu
3. Review detected models and their status
4. Click **Download** for missing models, or **Download All Missing**

For models without detected URLs:
- Click **Search URL** to search HuggingFace and CivitAI
- Or paste a direct download URL and click **Go**

## Supported Model Types

- Checkpoints (SD1.5, SDXL, SD3, Flux)
- Diffusion Models (Wan, LongCat, HunyuanVideo)
- VAE
- LoRA / LoHa / LoKr
- Text Encoders (T5, CLIP)
- CLIP Vision
- ControlNet
- IP-Adapter
- Upscalers (ESRGAN, etc.)
- SAM / SAM2
- And more...

## Requirements

- ComfyUI
- Python 3.10+
- `requests`
- `huggingface_hub`

## License

MIT License
