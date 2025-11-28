"""
Server-side API endpoints for Workflow Models Downloader
"""

import os
import re
import json
import logging
import asyncio
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from aiohttp import web

import folder_paths
from server import PromptServer

# Get routes from ComfyUI server
routes = PromptServer.instance.routes

# Extension path
EXTENSION_PATH = os.path.dirname(__file__)

# Settings file path
SETTINGS_FILE = os.path.join(EXTENSION_PATH, 'settings.json')

# Search metadata cache file
SEARCH_CACHE_FILE = os.path.join(EXTENSION_PATH, 'search_cache.json')

# Download progress tracking
download_progress = {}
download_lock = threading.Lock()
cancelled_downloads = set()  # Track cancelled download IDs

# Download queue system
download_queue = []  # Queued downloads waiting to start
download_queue_lock = threading.Lock()
max_parallel_downloads = 3  # Default, configurable via settings
active_download_count = 0

# Model aliases file
MODEL_ALIASES_FILE = os.path.join(EXTENSION_PATH, 'metadata', 'model-aliases.json')

# Settings cache
_settings_cache = None

# Fuzzy matching imports
from difflib import SequenceMatcher
import subprocess
import shutil


def load_settings():
    """Load settings from settings.json"""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    default_settings = {
        'huggingface_token': '',
        'civitai_api_key': '',
        'tavily_api_key': '',
        'enable_advanced_search': False
    }

    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                # Merge with defaults
                _settings_cache = {**default_settings, **saved}
                return _settings_cache
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error loading settings: {e}")

    _settings_cache = default_settings
    return _settings_cache


def save_settings(settings):
    """Save settings to settings.json"""
    global _settings_cache
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        _settings_cache = settings
        logging.info("[Workflow-Models-Downloader] Settings saved")
        return True
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error saving settings: {e}")
        return False


def get_huggingface_token():
    """Get HuggingFace token from settings"""
    settings = load_settings()
    return settings.get('huggingface_token', '')


def get_civitai_api_key():
    """Get CivitAI API key from settings"""
    settings = load_settings()
    return settings.get('civitai_api_key', '')


def get_tavily_api_key():
    """Get Tavily API key from settings"""
    settings = load_settings()
    return settings.get('tavily_api_key', '')


def is_advanced_search_enabled():
    """Check if advanced search is enabled"""
    settings = load_settings()
    return settings.get('enable_advanced_search', False) and bool(settings.get('tavily_api_key', ''))


# Search metadata cache
_search_cache = None


def load_search_cache():
    """Load search metadata cache from file"""
    global _search_cache
    if _search_cache is not None:
        return _search_cache

    try:
        if os.path.exists(SEARCH_CACHE_FILE):
            with open(SEARCH_CACHE_FILE, 'r', encoding='utf-8') as f:
                _search_cache = json.load(f)
                return _search_cache
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error loading search cache: {e}")

    _search_cache = {}
    return _search_cache


def save_search_cache(cache):
    """Save search metadata cache to file"""
    global _search_cache
    try:
        with open(SEARCH_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
        _search_cache = cache
        return True
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error saving search cache: {e}")
        return False


def get_cached_metadata(filename):
    """Get cached search metadata for a filename"""
    cache = load_search_cache()
    return cache.get(filename)


def save_search_metadata(filename, metadata):
    """Save search metadata for a filename"""
    cache = load_search_cache()
    metadata['cached_at'] = json.dumps({"$date": str(os.path.getmtime(SEARCH_CACHE_FILE) if os.path.exists(SEARCH_CACHE_FILE) else 0)})
    import datetime
    metadata['cached_at'] = datetime.datetime.now().isoformat()
    cache[filename] = metadata
    save_search_cache(cache)


def _cache_download_url(filename, url, source, hf_repo=None, hf_path=None, model_name=None, civitai_url=None):
    """Cache URL after successful download for future use"""
    import datetime
    try:
        metadata = {
            'url': url,
            'source': f'download_{source}',
            'hf_repo': hf_repo or '',
            'hf_path': hf_path or '',
            'model_name': model_name or '',
            'civitai_url': civitai_url or '',
            'cached_at': datetime.datetime.now().isoformat(),
            'from_download': True
        }
        save_search_metadata(filename, metadata)
        logging.info(f"[Workflow-Models-Downloader] Cached URL for: {filename}")
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Failed to cache URL: {e}")


logging.info("[Workflow-Models-Downloader] Loading extension...")


# =============================================================================
# METADATA LOADING
# =============================================================================

# Cache for metadata
_model_list_cache = None
_extension_node_map_cache = None


def get_metadata_path():
    """Get path to metadata directory - check multiple locations"""
    # First check in our extension's metadata folder
    local_metadata = os.path.join(EXTENSION_PATH, 'metadata')
    if os.path.exists(local_metadata):
        return local_metadata

    # Check in comfyui_workflow_models_identifier
    identifier_path = os.path.join(os.path.dirname(folder_paths.base_path), 'comfyui_workflow_models_identifier', 'metadata')
    if os.path.exists(identifier_path):
        return identifier_path

    # Check ComfyUI Manager
    manager_path = os.path.join(folder_paths.base_path, 'custom_nodes', 'ComfyUI-Manager')
    if os.path.exists(manager_path):
        return manager_path

    return None


def load_model_list():
    """Load model-list.json from metadata"""
    global _model_list_cache
    if _model_list_cache is not None:
        return _model_list_cache

    metadata_path = get_metadata_path()
    if not metadata_path:
        logging.warning("[Workflow-Models-Downloader] Metadata path not found")
        _model_list_cache = []
        return _model_list_cache

    try:
        model_list_path = os.path.join(metadata_path, 'model-list.json')
        if os.path.exists(model_list_path):
            with open(model_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _model_list_cache = data.get('models', [])
                logging.info(f"[Workflow-Models-Downloader] Loaded {len(_model_list_cache)} models from model-list.json")
                return _model_list_cache
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error loading model-list.json: {e}")

    _model_list_cache = []
    return _model_list_cache


def load_extension_node_map():
    """Load extension-node-map.json from metadata"""
    global _extension_node_map_cache
    if _extension_node_map_cache is not None:
        return _extension_node_map_cache

    metadata_path = get_metadata_path()
    if not metadata_path:
        _extension_node_map_cache = {}
        return _extension_node_map_cache

    try:
        map_path = os.path.join(metadata_path, 'extension-node-map.json')
        if os.path.exists(map_path):
            with open(map_path, 'r', encoding='utf-8') as f:
                _extension_node_map_cache = json.load(f)
                logging.info(f"[Workflow-Models-Downloader] Loaded {len(_extension_node_map_cache)} extensions from extension-node-map.json")
                return _extension_node_map_cache
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error loading extension-node-map.json: {e}")

    _extension_node_map_cache = {}
    return _extension_node_map_cache


def lookup_model_in_model_list(filename):
    """Look up model info from model-list.json by filename"""
    models = load_model_list()
    filename_lower = filename.lower()

    for model in models:
        if model.get('filename', '').lower() == filename_lower:
            model_type = model.get('type', '')
            save_path = model.get('save_path', '')

            # Handle 'default' save_path - map to appropriate directory
            if save_path == 'default':
                type_to_dir = {
                    'upscale': 'upscale_models',
                    'TAESD': 'vae_approx',
                    'controlnet': 'controlnet',
                    'checkpoint': 'checkpoints',
                    'lora': 'loras',
                    'vae': 'vae',
                }
                save_path = type_to_dir.get(model_type, 'models')

            return model_type, save_path, model.get('url', ''), model.get('size', '')

    return None, None, None, None


def lookup_node_github_url(node_type):
    """Look up GitHub URL for a node type from extension-node-map.json"""
    node_map = load_extension_node_map()

    for github_url, node_data in node_map.items():
        if isinstance(node_data, list) and len(node_data) > 0:
            node_list = node_data[0] if isinstance(node_data[0], list) else []
            if node_type in node_list:
                return github_url

    return None


# Initialize metadata on load
logging.info("[Workflow-Models-Downloader] Initializing metadata...")
_metadata_path = get_metadata_path()
if _metadata_path:
    logging.info(f"[Workflow-Models-Downloader] Using metadata from: {_metadata_path}")
else:
    logging.warning("[Workflow-Models-Downloader] No metadata found - model detection may be limited")


# =============================================================================
# URL DETECTION - Multi-source lookup
# =============================================================================

# Cache for popular models registry
_popular_models_cache = None

# Cache for API search results
_url_search_cache = {}


def load_popular_models():
    """Load the curated popular-models.json registry"""
    global _popular_models_cache
    if _popular_models_cache is not None:
        return _popular_models_cache

    try:
        popular_path = os.path.join(EXTENSION_PATH, 'metadata', 'popular-models.json')
        if os.path.exists(popular_path):
            with open(popular_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _popular_models_cache = data.get('models', {})
                logging.info(f"[Workflow-Models-Downloader] Loaded {len(_popular_models_cache)} popular models")
                return _popular_models_cache
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Error loading popular-models.json: {e}")

    _popular_models_cache = {}
    return _popular_models_cache


def lookup_url_in_popular_models(filename):
    """Look up URL from curated popular models registry"""
    models = load_popular_models()
    filename_lower = filename.lower()

    # Exact match
    if filename in models:
        return models[filename].get('url', '')

    # Case-insensitive match
    for name, info in models.items():
        if name.lower() == filename_lower:
            return info.get('url', '')

    return None


def lookup_url_in_model_list(filename):
    """Look up URL from model-list.json with fuzzy matching"""
    models = load_model_list()
    filename_lower = filename.lower()
    filename_base = os.path.splitext(filename_lower)[0]

    # Exact match first
    for model in models:
        model_filename = model.get('filename', '')
        if model_filename.lower() == filename_lower:
            return model.get('url', '')

    # Fuzzy match - check if filename contains or is contained by model name
    for model in models:
        model_filename = model.get('filename', '')
        model_base = os.path.splitext(model_filename.lower())[0]

        # Check substring matches
        if filename_base in model_base or model_base in filename_base:
            url = model.get('url', '')
            if url:
                return url

    return None


def search_huggingface_api(filename):
    """Search HuggingFace API for a model file"""
    global _url_search_cache

    cache_key = f"hf_{filename}"
    if cache_key in _url_search_cache:
        return _url_search_cache[cache_key]

    try:
        import requests

        # Search for repos containing this filename
        filename_base = os.path.splitext(filename)[0]
        search_url = f"https://huggingface.co/api/models?search={urllib.parse.quote(filename_base)}&limit=5"

        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            repos = response.json()

            for repo in repos:
                repo_id = repo.get('id', '')
                if not repo_id:
                    continue

                # Check if this repo has the file
                files_url = f"https://huggingface.co/api/models/{repo_id}/tree/main"
                try:
                    files_response = requests.get(files_url, timeout=10)
                    if files_response.status_code == 200:
                        files = files_response.json()
                        for file_info in files:
                            if file_info.get('path', '').endswith(filename):
                                url = f"https://huggingface.co/{repo_id}/resolve/main/{file_info['path']}"
                                _url_search_cache[cache_key] = url
                                logging.info(f"[Workflow-Models-Downloader] Found {filename} on HuggingFace: {repo_id}")
                                return url
                except:
                    continue

    except Exception as e:
        logging.debug(f"[Workflow-Models-Downloader] HuggingFace API search failed: {e}")

    _url_search_cache[cache_key] = None
    return None


def search_civitai_api(filename):
    """Search CivitAI API for a model file"""
    global _url_search_cache

    cache_key = f"civit_{filename}"
    if cache_key in _url_search_cache:
        return _url_search_cache[cache_key]

    try:
        import requests

        # Search by filename
        filename_base = os.path.splitext(filename)[0]
        # Remove common suffixes for better search
        search_name = re.sub(r'[-_]?(fp16|fp8|bf16|e4m3fn|scaled|pruned|emaonly).*', '', filename_base, flags=re.IGNORECASE)

        search_url = f"https://civitai.com/api/v1/models?query={urllib.parse.quote(search_name)}&limit=5"

        response = requests.get(search_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])

            for item in items:
                model_versions = item.get('modelVersions', [])
                for version in model_versions:
                    files = version.get('files', [])
                    for file_info in files:
                        file_name = file_info.get('name', '')
                        if file_name.lower() == filename.lower():
                            url = file_info.get('downloadUrl', '')
                            if url:
                                _url_search_cache[cache_key] = url
                                logging.info(f"[Workflow-Models-Downloader] Found {filename} on CivitAI")
                                return url

    except Exception as e:
        logging.debug(f"[Workflow-Models-Downloader] CivitAI API search failed: {e}")

    _url_search_cache[cache_key] = None
    return None


def search_tavily_api(filename):
    """Search using Tavily API for model download URLs"""
    global _url_search_cache

    cache_key = f"tavily_{filename}"
    if cache_key in _url_search_cache:
        return _url_search_cache[cache_key]

    tavily_key = get_tavily_api_key()
    if not tavily_key:
        return None

    try:
        import requests

        # Build search query focused on finding download URLs
        filename_base = os.path.splitext(filename)[0]
        # Clean up common suffixes for better search
        search_name = re.sub(r'[-_]?(fp16|fp8|bf16|e4m3fn|scaled|pruned|emaonly).*', '', filename_base, flags=re.IGNORECASE)

        search_query = f"{search_name} safetensors download huggingface OR civitai"

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": tavily_key,
            "query": search_query,
            "search_depth": "advanced",
            "include_domains": ["huggingface.co", "civitai.com", "github.com"],
            "max_results": 10
        }

        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Look for direct download URLs in results
            for result in results:
                result_url = result.get('url', '')
                content = result.get('content', '').lower()
                title = result.get('title', '').lower()

                # Check if this looks like a model page or download link
                if 'huggingface.co' in result_url:
                    # Try to construct download URL from HuggingFace page
                    # Pattern: https://huggingface.co/{repo}/blob/main/{file}
                    hf_pattern = r'huggingface\.co/([^/]+/[^/]+)(?:/(?:blob|tree)/[^/]+)?'
                    match = re.search(hf_pattern, result_url)
                    if match:
                        repo = match.group(1)
                        # Check if filename is mentioned in content or title
                        if filename.lower() in content or filename_base.lower() in content:
                            # Try to find the file in this repo
                            try:
                                files_url = f"https://huggingface.co/api/models/{repo}/tree/main"
                                files_response = requests.get(files_url, timeout=10)
                                if files_response.status_code == 200:
                                    files = files_response.json()
                                    for file_info in files:
                                        file_path = file_info.get('path', '')
                                        if file_path.endswith('.safetensors') or file_path.endswith('.ckpt'):
                                            # Check if filename matches
                                            if filename.lower() in file_path.lower() or filename_base.lower() in file_path.lower():
                                                download_url = f"https://huggingface.co/{repo}/resolve/main/{file_path}"
                                                _url_search_cache[cache_key] = {
                                                    'url': download_url,
                                                    'source': 'tavily_huggingface',
                                                    'repo': repo,
                                                    'tavily_result': result
                                                }
                                                logging.info(f"[Workflow-Models-Downloader] Tavily found {filename} on HuggingFace: {repo}")
                                                return _url_search_cache[cache_key]
                            except:
                                pass

                elif 'civitai.com' in result_url:
                    # Extract model ID from CivitAI URL
                    civit_pattern = r'civitai\.com/models/(\d+)'
                    match = re.search(civit_pattern, result_url)
                    if match:
                        model_id = match.group(1)
                        # Get model info from CivitAI API
                        try:
                            api_url = f"https://civitai.com/api/v1/models/{model_id}"
                            api_response = requests.get(api_url, timeout=10)
                            if api_response.status_code == 200:
                                model_data = api_response.json()
                                model_versions = model_data.get('modelVersions', [])
                                for version in model_versions:
                                    files = version.get('files', [])
                                    for file_info in files:
                                        file_name = file_info.get('name', '')
                                        if filename.lower() in file_name.lower() or filename_base.lower() in file_name.lower():
                                            download_url = file_info.get('downloadUrl', '')
                                            if download_url:
                                                _url_search_cache[cache_key] = {
                                                    'url': download_url,
                                                    'source': 'tavily_civitai',
                                                    'model_name': model_data.get('name', ''),
                                                    'civitai_url': result_url,
                                                    'tavily_result': result
                                                }
                                                logging.info(f"[Workflow-Models-Downloader] Tavily found {filename} on CivitAI")
                                                return _url_search_cache[cache_key]
                        except:
                            pass

            # If no direct match found, return the most relevant result info
            if results:
                _url_search_cache[cache_key] = {
                    'url': None,
                    'results': results[:5],  # Return top 5 for user to choose
                    'source': 'tavily_suggestions'
                }
                return _url_search_cache[cache_key]

    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Tavily API search failed: {e}")

    _url_search_cache[cache_key] = None
    return None


def find_model_url(filename, search_apis=False):
    """
    Try to find download URL for a model using multiple sources:
    1. Popular models registry (curated list)
    2. model-list.json (ComfyUI Manager)
    3. HuggingFace API search (if search_apis=True)
    4. CivitAI API search (if search_apis=True)
    """
    # 1. Check popular models registry
    url = lookup_url_in_popular_models(filename)
    if url:
        return url, 'popular_models'

    # 2. Check model-list.json with fuzzy matching
    url = lookup_url_in_model_list(filename)
    if url:
        return url, 'model_list'

    # 3. Search HuggingFace API
    if search_apis:
        url = search_huggingface_api(filename)
        if url:
            return url, 'huggingface_api'

        # 4. Search CivitAI API
        url = search_civitai_api(filename)
        if url:
            return url, 'civitai_api'

    return None, None


# =============================================================================
# MODEL TYPE DETECTION
# =============================================================================

SUPPORTED_MODEL_EXTENSIONS = {'.ckpt', '.pt', '.pt2', '.bin', '.pth', '.safetensors', '.pkl', '.sft', '.gguf', '.onnx'}

# Filename patterns for model type detection
# Patterns are checked in order - first match wins
# This must match exactly with parse_workflow_models.py
FILENAME_TYPE_PATTERNS = [
    # VAE Approximation (TAESD)
    (r'tae[sf]\d*[_-]?(decoder|encoder)', 'TAESD', 'vae_approx'),

    # Latent upscalers (before generic upscale)
    (r'latent.*upsampl|upsampl.*latent', 'Latent Upsampler', 'latent_upscale_models'),

    # Text encoders (T5 variants)
    (r't5[-_]?xxl|umt5|t5[-_]?xl|t5[-_]?base', 'Text Encoder (T5)', 'text_encoders'),
    (r'long[-_]?clip', 'Long CLIP', 'text_encoders'),

    # CLIP Vision (before generic CLIP)
    (r'clip.*vision|sigclip.*vision|vision.*clip', 'CLIP Vision', 'clip_vision'),

    # CLIP models
    (r'^clip[-_]|clip[-_][lg]|openclip', 'CLIP', 'clip'),

    # Flux specific
    (r'^flux.*dev|flux.*schnell|^flux1|flux[-_]', 'Flux UNET', 'diffusion_models'),
    (r'^ae\.safetensors$', 'VAE (Flux)', 'vae'),

    # VAE (check before video models since video models can have _vae suffix)
    (r'_vae_|_vae\.|^vae[-_]|[-_]vae\.|vae[-_]?fp', 'VAE', 'vae'),

    # LoRA (check BEFORE video models - distill_lora, refinement_lora, etc. are LoRAs even with video model names)
    (r'lora|locon|dora', 'LoRA', 'loras'),

    # Video/Diffusion models (check patterns from VIDEO_MODEL_PATTERNS)
    (r'hunyuan|longcat|wanvideo|wan_|cosmos|cogvideo|mochi|ltxv|ltx[-_]?video', 'Video Diffusion Model', 'diffusion_models'),
    (r'framepack|stable[-_]?cascade|cascade[-_]', 'Video/Image Diffusion Model', 'diffusion_models'),
    (r'dynamicrafter|tooncrafter|animate', 'Animation Model', 'diffusion_models'),
    (r'svd|video[-_]?diffusion|i2v|t2v|ti2v', 'Video Diffusion Model', 'diffusion_models'),

    # ControlNet and adapters
    (r'controlnet|control[-_]?net|cn[-_]', 'ControlNet', 'controlnet'),
    (r't2i[-_]?adapter|adapter[-_]?t2i', 'T2I-Adapter', 'controlnet'),
    (r'ipadapter|ip[-_]?adapter', 'IP-Adapter', 'ipadapter'),

    # Face/Identity models
    (r'instantid', 'InstantID', 'instantid'),
    (r'pulid', 'PuLID', 'pulid'),
    (r'photomaker', 'PhotoMaker', 'photomaker'),
    (r'insightface|antelopev2|buffalo', 'InsightFace', 'insightface/models'),
    (r'gfpgan|codeformer|facerestorer', 'Face Restore', 'facerestore_models'),

    # Segmentation models
    (r'sam[-_]?2\.1|sam2\.1', 'SAM 2.1', 'sams'),
    (r'sam[-_]?2|sam2', 'SAM 2', 'sams'),
    (r'^sam[-_]|segment[-_]?anything', 'SAM', 'sams'),
    (r'grounding[-_]?dino', 'GroundingDINO', 'groundingdino'),
    (r'yolo|ultralytics', 'Ultralytics', 'ultralytics'),

    # VAE
    (r'vae|variational', 'VAE', 'vae'),

    # Upscalers
    (r'esrgan|realesrgan|swinir|upscale|4x[-_]|2x[-_]|rgt', 'Upscaler', 'upscale_models'),

    # AnimateDiff
    (r'animatediff|motion[-_]?module|mm[-_]?', 'AnimateDiff', 'animatediff_models'),
    (r'motion[-_]?lora', 'Motion LoRA', 'animatediff_motion_lora'),

    # Depth models
    (r'depth[-_]?anything|depthanything', 'Depth Anything', 'depthanything'),
    (r'depth[-_]?pro|ml[-_]?depth', 'Depth Pro', 'depth/ml-depth-pro'),

    # Embeddings
    (r'embedding|textual[-_]?inversion', 'Embedding', 'embeddings'),

    # SDXL checkpoints
    (r'sdxl|sd[-_]?xl|xl[-_]turbo', 'Checkpoint (SDXL)', 'checkpoints'),

    # SD 1.5/2.x checkpoints
    (r'sd[-_]?1\.?5|sd15|v1[-_]?5', 'Checkpoint (SD1.5)', 'checkpoints'),
    (r'sd[-_]?2\.?1|sd21|v2[-_]?1', 'Checkpoint (SD2.1)', 'checkpoints'),

    # SD3
    (r'sd[-_]?3|sd3', 'Checkpoint (SD3)', 'checkpoints'),

    # Inpainting
    (r'inpaint', 'Inpaint Model', 'checkpoints'),
]

# URL path to directory mapping
URL_DIRECTORY_HINTS = {
    '/diffusion_models/': 'diffusion_models',
    '/latent_upscale_models/': 'latent_upscale_models',
    '/text_encoders/': 'text_encoders',
    '/clip_vision/': 'clip_vision',
    '/controlnet/': 'controlnet',
    '/checkpoints/': 'checkpoints',
    '/loras/': 'loras',
    '/vae/': 'vae',
    '/vae_approx/': 'vae_approx',
    '/upscale_models/': 'upscale_models',
    '/embeddings/': 'embeddings',
    '/animatediff_models/': 'animatediff_models',
    '/animatediff_motion_lora/': 'animatediff_motion_lora',
    '/ipadapter/': 'ipadapter',
    '/insightface/': 'insightface/models',
    '/instantid/': 'instantid',
    '/photomaker/': 'photomaker',
    '/sams/': 'sams',
    '/ultralytics/': 'ultralytics',
    '/groundingdino/': 'groundingdino',
    '/facerestore_models/': 'facerestore_models',
    '/facedetection/': 'facedetection',
    '/depthanything/': 'depthanything',
    '/hypernetworks/': 'hypernetworks',
    '/gligen/': 'gligen',
    '/style_models/': 'style_models',
    '/unet/': 'unet',
    '/pulid/': 'pulid',
}


def identify_model_type_from_filename(model_name):
    """Identify model type from filename patterns"""
    model_lower = model_name.lower()

    # Skip GGUF/LLM files
    if model_lower.endswith('.gguf'):
        return None, None

    # First check model-list.json for exact match (from metadata)
    list_type, list_dir, list_url, list_size = lookup_model_in_model_list(model_name)
    if list_type and list_dir:
        return list_type, list_dir

    # Check against filename patterns
    for pattern, model_type, directory in FILENAME_TYPE_PATTERNS:
        if re.search(pattern, model_lower):
            return model_type, directory

    # Default fallback by extension
    ext = os.path.splitext(model_name)[1].lower()
    if ext in {'.safetensors', '.ckpt'}:
        return 'Checkpoint', 'checkpoints'
    elif ext == '.onnx':
        return 'ONNX Model', 'onnx'
    elif ext in SUPPORTED_MODEL_EXTENSIONS:
        return 'Model', 'models'
    else:
        return None, None


def calculate_file_hash(filepath, algorithm='sha256'):
    """Calculate SHA256 hash of a file (first 10MB for speed)"""
    import hashlib
    hash_obj = hashlib.new(algorithm)

    try:
        with open(filepath, 'rb') as f:
            # Read first 10MB for quick hash (CivitAI uses full file hash though)
            # For accurate lookup, we need the full hash
            while chunk := f.read(8192 * 1024):  # 8MB chunks
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Hash calculation error: {e}")
        return None


def lookup_civitai_by_hash(file_hash):
    """Look up model on CivitAI by SHA256 hash"""
    if not file_hash:
        return None

    try:
        import requests
        url = f"https://civitai.com/api/v1/model-versions/by-hash/{file_hash}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()

            # Extract relevant info
            model_info = {
                'model_name': data.get('model', {}).get('name', 'Unknown'),
                'model_type': data.get('model', {}).get('type', 'Unknown'),
                'version_name': data.get('name', ''),
                'model_id': data.get('modelId'),
                'version_id': data.get('id'),
                'download_url': None,
                'original_filename': None
            }

            # Find download URL from files
            files = data.get('files', [])
            for f in files:
                hashes = f.get('hashes', {})
                if hashes.get('SHA256', '').lower() == file_hash.lower():
                    model_info['download_url'] = f.get('downloadUrl')
                    model_info['original_filename'] = f.get('name')
                    break

            # Fallback to first file if hash match not found
            if not model_info['download_url'] and files:
                model_info['download_url'] = files[0].get('downloadUrl')
                model_info['original_filename'] = files[0].get('name')

            return model_info

        return None
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] CivitAI hash lookup error: {e}")
        return None


def find_model_file_path(target_dir, filename):
    """Find the full path to a model file, checking all configured model paths including extra_model_paths.yaml"""

    dirs_to_check = [target_dir]
    if target_dir in EQUIVALENT_DIRECTORIES:
        dirs_to_check = EQUIVALENT_DIRECTORIES[target_dir]

    for check_dir in dirs_to_check:
        # Get all configured paths for this folder type (includes extra_model_paths.yaml)
        try:
            all_paths = folder_paths.get_folder_paths(check_dir)
        except:
            # Fallback to default models_dir if folder type not found
            all_paths = [os.path.join(folder_paths.models_dir, check_dir)]

        for base_path in all_paths:
            # Check exact path
            model_path = os.path.join(base_path, filename)
            if os.path.exists(model_path):
                return model_path

            # Search subdirectories
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if filename in files:
                        return os.path.join(root, filename)

    return None


def extract_huggingface_info(url):
    """Extract HuggingFace repo and filename from URL"""
    if not url or 'huggingface.co' not in url:
        return None, None

    # Clean URL
    url = url.split(')')[0].replace('\\n', '').replace('\n', '').strip()

    # Pattern: https://huggingface.co/{repo}/resolve/{branch}/{path/to/file}
    pattern = r'huggingface\.co/([^/]+/[^/]+)/(?:resolve|blob)/[^/]+/(.+?)(?:\?|$)'
    match = re.search(pattern, url)

    if match:
        repo = match.group(1)
        filepath = match.group(2)
        return repo, filepath

    return None, None


# ComfyUI equivalent directories - these share the same search path
EQUIVALENT_DIRECTORIES = {
    'text_encoders': ['clip', 'text_encoders'],
    'clip': ['clip', 'text_encoders'],
    'unet': ['unet', 'diffusion_models'],
    'diffusion_models': ['unet', 'diffusion_models'],
}

# Model format alternatives - used to find compatible alternatives
MODEL_FORMAT_PATTERNS = [
    # (pattern_to_match, alternative_suffixes_to_try)
    (r'(.+?)[-_]?fp32\.safetensors$', ['fp16', 'bf16', 'fp8', 'fp8_e4m3fn', 'gguf']),
    (r'(.+?)[-_]?fp16\.safetensors$', ['fp32', 'bf16', 'fp8', 'fp8_e4m3fn', 'gguf']),
    (r'(.+?)[-_]?bf16\.safetensors$', ['fp16', 'fp32', 'fp8', 'fp8_e4m3fn', 'gguf']),
    (r'(.+?)[-_]?fp8[-_]?e4m3fn\.safetensors$', ['fp16', 'bf16', 'fp8', 'fp32']),
    (r'(.+?)[-_]?fp8\.safetensors$', ['fp16', 'bf16', 'fp8_e4m3fn', 'fp32']),
    (r'(.+?)\.gguf$', ['safetensors', 'fp16.safetensors', 'bf16.safetensors']),
    (r'(.+?)[-_]?Q\d+.*\.gguf$', ['safetensors', 'fp16.safetensors', 'gguf']),
    (r'(.+?)\.safetensors$', ['fp16.safetensors', 'bf16.safetensors', 'fp8.safetensors', 'gguf']),
]


def find_model_alternatives(filename, target_dir):
    """Find alternative versions of a model (different quantizations/formats)"""
    alternatives = []
    filename_lower = filename.lower()
    base_name = None

    # Try to extract base name from filename
    for pattern, alt_suffixes in MODEL_FORMAT_PATTERNS:
        match = re.match(pattern, filename_lower)
        if match:
            base_name = match.group(1)
            break

    if not base_name:
        # Try simple extension removal
        base_name = os.path.splitext(filename_lower)[0]
        # Remove common suffixes
        for suffix in ['_fp16', '_fp32', '_bf16', '_fp8', '-fp16', '-fp32', '-bf16', '-fp8']:
            if base_name.endswith(suffix):
                base_name = base_name[:-len(suffix)]
                break

    # Get list of directories to check
    dirs_to_check = [target_dir]
    if target_dir in EQUIVALENT_DIRECTORIES:
        dirs_to_check = EQUIVALENT_DIRECTORIES[target_dir]

    for check_dir in dirs_to_check:
        try:
            available_files = folder_paths.get_filename_list(check_dir)

            for available_file in available_files:
                available_lower = available_file.lower()
                available_base = os.path.splitext(os.path.basename(available_lower))[0]

                # Remove common suffixes for comparison
                for suffix in ['_fp16', '_fp32', '_bf16', '_fp8', '-fp16', '-fp32', '-bf16', '-fp8', '_fp8_e4m3fn']:
                    if available_base.endswith(suffix):
                        available_base = available_base[:-len(suffix)]
                        break

                # Check if this could be an alternative
                if available_file.lower() != filename_lower:
                    # Check if base names are similar
                    if base_name in available_base or available_base in base_name:
                        # Get full path and size
                        full_path = folder_paths.get_full_path(check_dir, available_file)
                        size_str = None
                        if full_path and os.path.exists(full_path):
                            try:
                                size_bytes = os.path.getsize(full_path)
                                size_mb = size_bytes / (1024 * 1024)
                                if size_mb >= 1024:
                                    size_str = f"{size_mb/1024:.2f} GB"
                                else:
                                    size_str = f"{size_mb:.1f} MB"
                            except:
                                pass

                        # Determine format type
                        format_type = 'unknown'
                        if 'gguf' in available_lower:
                            format_type = 'GGUF'
                        elif 'fp16' in available_lower:
                            format_type = 'FP16'
                        elif 'bf16' in available_lower:
                            format_type = 'BF16'
                        elif 'fp8' in available_lower:
                            format_type = 'FP8'
                        elif 'fp32' in available_lower:
                            format_type = 'FP32'
                        elif available_lower.endswith('.safetensors'):
                            format_type = 'SafeTensors'

                        alternatives.append({
                            'filename': available_file,
                            'directory': check_dir,
                            'format': format_type,
                            'size': size_str
                        })
        except Exception as e:
            logging.debug(f"[WMD] Error finding alternatives in {check_dir}: {e}")

    return alternatives[:5]  # Return top 5 alternatives


def check_model_exists(target_dir, filename):
    """Check if model file exists using ComfyUI's folder_paths system.
    This ensures we match exactly what ComfyUI can find and load."""

    # Get list of directories to check (including equivalent ones)
    dirs_to_check = [target_dir]
    if target_dir in EQUIVALENT_DIRECTORIES:
        dirs_to_check = EQUIVALENT_DIRECTORIES[target_dir]

    for check_dir in dirs_to_check:
        try:
            # Use ComfyUI's get_filename_list which returns all files ComfyUI can find
            # This respects extra_model_paths.yaml and subdirectory structure
            available_files = folder_paths.get_filename_list(check_dir)

            # Check if the exact filename is in the list
            # ComfyUI returns files with relative paths like "subfolder/file.safetensors"
            # We only match exact paths - if workflow says "model.safetensors" but file is at
            # "subfolder/model.safetensors", it won't work in ComfyUI either
            if filename in available_files:
                # Found it - get the full path to check size
                full_path = folder_paths.get_full_path(check_dir, filename)
                if full_path and os.path.exists(full_path):
                    try:
                        size_bytes = os.path.getsize(full_path)
                        size_mb = size_bytes / (1024 * 1024)
                        if size_mb >= 1024:
                            return True, f"{size_mb/1024:.2f} GB"
                        else:
                            return True, f"{size_mb:.1f} MB"
                    except:
                        return True, None
        except Exception as e:
            # Fallback: folder type might not exist in ComfyUI
            logging.debug(f"[WMD] Could not check {check_dir}: {e}")
            continue

    return False, None


def scan_workflow_for_models(workflow_json):
    """Scan workflow JSON for model references"""
    if isinstance(workflow_json, str):
        try:
            workflow_data = json.loads(workflow_json)
        except:
            workflow_data = {}
        content = workflow_json
    else:
        workflow_data = workflow_json
        content = json.dumps(workflow_json)

    # First, extract models from node properties (the proper way)
    # ComfyUI stores model info in node.properties.models array
    node_models = {}  # filename -> {url, directory, node_type}

    # Collect all nodes including from subgraphs
    all_nodes = list(workflow_data.get('nodes', []))

    # Also check subgraph definitions for nested nodes
    definitions = workflow_data.get('definitions', {})
    subgraphs = definitions.get('subgraphs', [])
    for subgraph in subgraphs:
        subgraph_nodes = subgraph.get('nodes', [])
        all_nodes.extend(subgraph_nodes)

    for node in all_nodes:
        node_type = node.get('type', '')
        properties = node.get('properties', {})
        models_list = properties.get('models', [])

        for model_info in models_list:
            if isinstance(model_info, dict):
                name = model_info.get('name', '')
                url = model_info.get('url', '')
                directory = model_info.get('directory', '')

                if name and name not in node_models:
                    node_models[name] = {
                        'url': url,
                        'directory': directory,
                        'node_type': node_type
                    }

    # Also check widgets_values for model filenames
    for node in all_nodes:
        node_type = node.get('type', '')
        widgets_values = node.get('widgets_values', [])

        for value in widgets_values:
            if isinstance(value, str) and any(value.endswith(ext) for ext in ['.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.onnx']):
                # Skip GGUF
                if value.lower().endswith('.gguf'):
                    continue
                if value not in node_models:
                    node_models[value] = {
                        'url': '',
                        'directory': '',
                        'node_type': node_type
                    }

    # Find model filenames via regex (fallback for markdown notes, etc.)
    model_pattern = r'([\w\-\.%]+\.(?:safetensors|ckpt|pt|pth|bin|onnx))'
    model_files_raw = re.findall(model_pattern, content)

    # Clean and deduplicate, decode URL-encoded names
    model_files = set()
    model_name_map = {}  # Map decoded name -> original name (for URL matching)

    # First, add all models from node properties (these are authoritative)
    for model_name in node_models.keys():
        if model_name and not model_name.lower().endswith('.gguf'):
            model_files.add(model_name)
            model_name_map[model_name] = model_name

    for model in model_files_raw:
        cleaned = model.strip()
        if cleaned and cleaned[0].isalnum():
            # Skip GGUF files
            if not cleaned.lower().endswith('.gguf'):
                # Decode URL-encoded characters (%2D -> -, %20 -> space, etc.)
                try:
                    decoded = urllib.parse.unquote(cleaned)
                except:
                    decoded = cleaned

                model_files.add(decoded)
                model_name_map[decoded] = cleaned  # Keep original for URL matching

    # Find download URLs via regex
    url_pattern = r'(https?://(?:huggingface\.co|civitai\.com|github\.com)[^\s"\'<>\)]+)'
    urls = re.findall(url_pattern, content)

    # Clean URLs
    cleaned_urls = []
    for url in urls:
        url = url.split(')')[0].replace('\\n', '').replace('\n', '').strip()
        if url:
            cleaned_urls.append(url)

    # Match models with URLs - check both decoded and original (URL-encoded) names
    model_url_map = {}
    for model in model_files:
        # First check if we have URL from node properties
        if model in node_models and node_models[model].get('url'):
            model_url_map[model] = node_models[model]['url']
            continue

        original_name = model_name_map.get(model, model)

        for url in cleaned_urls:
            # Check decoded name in URL
            if model in url:
                model_url_map[model] = url
                break
            # Check original (possibly URL-encoded) name in URL
            if original_name in url:
                model_url_map[model] = url
                break
            # Check URL-encoded version of decoded name
            encoded_model = urllib.parse.quote(model, safe='')
            if encoded_model in url:
                model_url_map[model] = url
                break
            # Check without extension
            model_base = model.replace('.safetensors', '').replace('.ckpt', '')
            if model_base in url or urllib.parse.quote(model_base, safe='') in url:
                model_url_map[model] = url
                break

    # Build results
    models_data = []
    for model in sorted(model_files):
        url = model_url_map.get(model, '')

        # Get model type and directory from filename patterns
        model_type, target_dir = identify_model_type_from_filename(model)

        if model_type is None:
            continue  # Skip unknown types

        # Check if this model was found in node properties (authoritative source)
        from_node_properties = model in node_models

        # First priority: use directory from node properties if available
        if from_node_properties and node_models[model].get('directory'):
            target_dir = node_models[model]['directory']

        # Second priority: Check URL for directory hints
        elif url:
            url_lower = url.lower()
            for url_path, directory in URL_DIRECTORY_HINTS.items():
                if url_path.lower() in url_lower:
                    target_dir = directory
                    break

        # Check for cached search metadata first
        cached_metadata = get_cached_metadata(model)

        # If no URL found, try to find one from our registries (not API search - that's manual)
        url_source = None
        if not url:
            # First check cache for previously downloaded/found URLs
            if cached_metadata and cached_metadata.get('url'):
                url = cached_metadata['url']
                url_source = cached_metadata.get('source', 'cached')
            else:
                found_url, url_source = find_model_url(model, search_apis=False)
                if found_url:
                    url = found_url

        # Extract HuggingFace info
        hf_repo, hf_path = extract_huggingface_info(url)

        # If we got URL from cache, also get hf_repo/hf_path from cache
        if cached_metadata and not hf_repo:
            hf_repo = cached_metadata.get('hf_repo', '')
            hf_path = cached_metadata.get('hf_path', '')

        # Check if model exists
        exists, local_size = check_model_exists(target_dir, model)

        # Skip models found only via regex that have no URL and don't exist locally
        # These are likely false positives from markdown notes or comments
        if not from_node_properties and not url and not exists:
            continue

        # Get node type from node_models if available
        node_type = node_models.get(model, {}).get('node_type', '')

        # Determine source
        if hf_repo:
            source = 'HuggingFace'
        elif url and 'civitai.com' in url:
            source = 'CivitAI'
        elif url_source:
            source = url_source
        else:
            source = 'Unknown'

        # Find alternatives if model doesn't exist
        alternatives = []
        if not exists:
            alternatives = find_model_alternatives(model, target_dir)

        models_data.append({
            'filename': model,
            'type': model_type,
            'directory': target_dir,
            'full_path': os.path.join(folder_paths.models_dir, target_dir, model),
            'exists': exists,
            'local_size': local_size or '',
            'source': source,
            'url': url,
            'hf_repo': hf_repo or '',
            'hf_path': hf_path or '',
            'node_type': node_type,
            'url_source': url_source or ('workflow' if url else None),
            'search_metadata': cached_metadata,
            'alternatives': alternatives
        })

    return models_data


# =============================================================================
# API ENDPOINTS
# =============================================================================

@routes.post("/workflow-models/scan")
async def scan_workflow(request):
    """Scan the provided workflow JSON for models"""
    try:
        data = await request.json()
        workflow = data.get('workflow', {})

        if not workflow:
            return web.json_response({'error': 'No workflow provided'}, status=400)

        models = scan_workflow_for_models(workflow)

        # Calculate summary
        total = len(models)
        existing = sum(1 for m in models if m['exists'])
        missing = total - existing
        hf_models = [m for m in models if m['source'] == 'HuggingFace']

        return web.json_response({
            'success': True,
            'models': models,
            'summary': {
                'total': total,
                'existing': existing,
                'missing': missing,
                'hf_downloadable': len([m for m in hf_models if not m['exists']])
            }
        })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Scan error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/directories")
async def get_available_directories(request):
    """Get available model directories including extra_model_paths"""
    try:
        # Standard model folder types (curated list)
        all_types = set([
            'checkpoints', 'clip', 'clip_vision', 'controlnet', 'diffusion_models',
            'embeddings', 'gligen', 'hypernetworks', 'ipadapter', 'loras',
            'style_models', 'text_encoders', 'unet', 'upscale_models', 'vae',
            'photomaker', 'instantid', 'pulid', 'sams', 'animatediff_models',
            'ultralytics', 'mmdets', 'onnx', 'reactor', 'facerestore_models',
            'facedetection', 'liveportrait', 'inpaint', 'xlabs', 'LLM',
            'llm_gguf', 'CogVideo', 'blip'
        ])

        # Folders to exclude (not model folders)
        EXCLUDED_FOLDERS = {
            'custom_nodes', 'configs', 'fonts', 'kjnodes_fonts', 'web', 'js',
            'user', 'input', 'output', 'temp', 'models', 'pycache'
        }

        # Add custom folder types, excluding non-model folders
        if hasattr(folder_paths, 'folder_names_and_paths'):
            for folder_type in folder_paths.folder_names_and_paths.keys():
                if folder_type.lower() in EXCLUDED_FOLDERS:
                    continue
                if any(x in folder_type.lower() for x in ['pycache', '_cache', 'config', 'font']):
                    continue
                all_types.add(folder_type)

        available = []
        for folder_type in all_types:
            try:
                paths = folder_paths.get_folder_paths(folder_type)
                if paths:
                    available.append({
                        'name': folder_type,
                        'paths': paths,
                        'has_extra_paths': len(paths) > 1
                    })
            except:
                # Folder type not registered, skip
                pass

        # Sort alphabetically
        available.sort(key=lambda x: x['name'])

        return web.json_response({
            'success': True,
            'directories': available
        })
    except Exception as e:
        logging.error(f"[WMD] Get directories error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/debug-paths")
async def debug_model_paths(request):
    """Debug endpoint to show all model paths ComfyUI knows about"""
    try:
        paths_info = {}
        folder_types = ['checkpoints', 'loras', 'vae', 'controlnet', 'clip', 'text_encoders',
                        'diffusion_models', 'unet', 'embeddings', 'upscale_models', 'clip_vision']

        for folder_type in folder_types:
            try:
                paths = folder_paths.get_folder_paths(folder_type)
                file_count = len(folder_paths.get_filename_list(folder_type))
                paths_info[folder_type] = {
                    'paths': paths,
                    'file_count': file_count
                }
            except Exception as e:
                paths_info[folder_type] = {
                    'paths': [],
                    'file_count': 0,
                    'error': str(e)
                }

        return web.json_response({
            'success': True,
            'models_dir': folder_paths.models_dir,
            'folder_paths': paths_info
        })
    except Exception as e:
        logging.error(f"[WMD] Debug paths error: {e}")
        return web.json_response({'error': str(e)}, status=500)


# Track which models have been used in workflows (for unused detection)
used_models_tracking = {}  # filename -> { last_used: timestamp, workflows: [list of workflow names] }

# Cache file path
USAGE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "usage_cache.json")


def load_usage_cache():
    """Load usage tracking from persistent cache"""
    global used_models_tracking
    try:
        if os.path.exists(USAGE_CACHE_FILE):
            with open(USAGE_CACHE_FILE, 'r', encoding='utf-8') as f:
                used_models_tracking = json.load(f)
            logging.info(f"[WMD] Loaded usage cache with {len(used_models_tracking)} models")
    except Exception as e:
        logging.error(f"[WMD] Error loading usage cache: {e}")
        used_models_tracking = {}


def save_usage_cache():
    """Save usage tracking to persistent cache"""
    global used_models_tracking
    try:
        with open(USAGE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(used_models_tracking, f, indent=2)
        logging.info(f"[WMD] Saved usage cache with {len(used_models_tracking)} models")
    except Exception as e:
        logging.error(f"[WMD] Error saving usage cache: {e}")


# Load cache on module import
load_usage_cache()


def extract_models_from_workflow(workflow_data):
    """Extract model filenames from a workflow JSON"""
    models = set()

    def extract_from_node(node):
        if isinstance(node, dict):
            widgets = node.get('widgets_values', [])
            if widgets:
                for val in widgets:
                    if isinstance(val, str) and (val.endswith('.safetensors') or val.endswith('.ckpt') or
                                                   val.endswith('.pt') or val.endswith('.pth') or
                                                   val.endswith('.bin') or val.endswith('.gguf')):
                        models.add(val)

    # Handle both graph format and API format
    nodes = workflow_data.get('nodes', [])
    if isinstance(nodes, list):
        for node in nodes:
            extract_from_node(node)

    # Also check 'workflow' key if present (embedded in PNG metadata)
    if 'workflow' in workflow_data:
        nested = workflow_data['workflow']
        if isinstance(nested, dict) and 'nodes' in nested:
            for node in nested.get('nodes', []):
                extract_from_node(node)

    return models


@routes.post("/workflow-models/track-usage")
async def track_model_usage(request):
    """Track which models are used in the current workflow"""
    global used_models_tracking
    import time

    try:
        data = await request.json()
        models = data.get('models', [])
        workflow_name = data.get('workflow_name', 'current')

        timestamp = time.time()
        for model in models:
            filename = model.get('filename', '')
            if filename:
                if filename not in used_models_tracking:
                    used_models_tracking[filename] = {'last_used': timestamp, 'workflows': []}
                else:
                    used_models_tracking[filename]['last_used'] = timestamp

                # Add workflow to list if not already there
                workflows = used_models_tracking[filename].get('workflows', [])
                if workflow_name and workflow_name not in workflows:
                    workflows.append(workflow_name)
                    used_models_tracking[filename]['workflows'] = workflows[-10:]  # Keep last 10

        # Save to persistent cache
        save_usage_cache()

        return web.json_response({'success': True, 'tracked': len(models)})
    except Exception as e:
        logging.error(f"[WMD] Track usage error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/unused")
async def get_unused_models(request):
    """Get list of installed models that haven't been used recently"""
    global used_models_tracking

    try:
        # Get all installed models
        all_models = []
        folder_types = ['checkpoints', 'loras', 'vae', 'controlnet', 'clip', 'text_encoders',
                        'diffusion_models', 'unet', 'embeddings', 'upscale_models']

        for folder_type in folder_types:
            try:
                files = folder_paths.get_filename_list(folder_type)
                for filename in files:
                    full_path = folder_paths.get_full_path(folder_type, filename)
                    size_str = None
                    modified_time = None

                    if full_path and os.path.exists(full_path):
                        try:
                            stat = os.stat(full_path)
                            size_bytes = stat.st_size
                            size_mb = size_bytes / (1024 * 1024)
                            if size_mb >= 1024:
                                size_str = f"{size_mb/1024:.2f} GB"
                            else:
                                size_str = f"{size_mb:.1f} MB"
                            modified_time = stat.st_mtime
                        except:
                            pass

                    # Check if model was used (handle both old and new format)
                    usage_info = used_models_tracking.get(filename)
                    if isinstance(usage_info, dict):
                        is_used = True
                        last_used = usage_info.get('last_used')
                        workflows = usage_info.get('workflows', [])
                    elif usage_info is not None:
                        # Old format (just timestamp)
                        is_used = True
                        last_used = usage_info
                        workflows = []
                    else:
                        is_used = False
                        last_used = None
                        workflows = []

                    all_models.append({
                        'filename': filename,
                        'type': folder_type,
                        'size': size_str,
                        'modified': modified_time,
                        'last_used': last_used,
                        'is_used': is_used,
                        'workflows': workflows
                    })
            except:
                pass

        # Sort by unused first, then by size (largest first)
        unused_models = [m for m in all_models if not m['is_used']]
        unused_models.sort(key=lambda x: -(x.get('modified') or 0))

        return web.json_response({
            'success': True,
            'total_models': len(all_models),
            'unused_count': len(unused_models),
            'unused_models': unused_models,
            'tracked_count': len(used_models_tracking)
        })
    except Exception as e:
        logging.error(f"[WMD] Unused models error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/scan-all-workflows")
async def scan_all_workflows(request):
    """Scan all workflow files in a directory to build usage cache"""
    global used_models_tracking
    import time
    import glob

    try:
        data = await request.json()
        directory = data.get('directory', '')

        # Default to ComfyUI user directory
        if not directory:
            directory = os.path.join(folder_paths.base_path, 'user', 'default', 'workflows')
            if not os.path.exists(directory):
                # Try output directory
                directory = os.path.join(folder_paths.base_path, 'output')

        if not os.path.exists(directory):
            return web.json_response({
                'error': f'Directory not found: {directory}',
                'default_path': directory
            }, status=400)

        # Find all JSON files
        json_files = glob.glob(os.path.join(directory, '**', '*.json'), recursive=True)
        logging.info(f"[WMD] Scanning {len(json_files)} workflow files in {directory}")

        scanned = 0
        errors = 0
        models_found = set()
        timestamp = time.time()

        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)

                # Extract models from workflow
                workflow_models = extract_models_from_workflow(workflow_data)
                workflow_name = os.path.basename(filepath)

                for model in workflow_models:
                    models_found.add(model)
                    if model not in used_models_tracking:
                        used_models_tracking[model] = {'last_used': timestamp, 'workflows': []}

                    workflows = used_models_tracking[model].get('workflows', [])
                    if workflow_name not in workflows:
                        workflows.append(workflow_name)
                        used_models_tracking[model]['workflows'] = workflows[-10:]  # Keep last 10
                    used_models_tracking[model]['last_used'] = timestamp

                scanned += 1
            except Exception as e:
                logging.debug(f"[WMD] Error scanning {filepath}: {e}")
                errors += 1

        # Save to persistent cache
        save_usage_cache()

        return web.json_response({
            'success': True,
            'directory': directory,
            'workflows_scanned': scanned,
            'workflows_errored': errors,
            'models_found': len(models_found),
            'total_tracked': len(used_models_tracking)
        })
    except Exception as e:
        logging.error(f"[WMD] Scan all workflows error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/clear-cache")
async def clear_usage_cache(request):
    """Clear the usage tracking cache"""
    global used_models_tracking

    try:
        used_models_tracking = {}

        # Delete cache file
        if os.path.exists(USAGE_CACHE_FILE):
            os.remove(USAGE_CACHE_FILE)
            logging.info("[WMD] Usage cache cleared and file deleted")

        return web.json_response({
            'success': True,
            'message': 'Usage cache cleared'
        })
    except Exception as e:
        logging.error(f"[WMD] Clear cache error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/cache-info")
async def get_cache_info(request):
    """Get information about the usage cache"""
    global used_models_tracking

    try:
        cache_size = 0
        if os.path.exists(USAGE_CACHE_FILE):
            cache_size = os.path.getsize(USAGE_CACHE_FILE)

        # Get default workflow directories
        default_dirs = []
        user_workflows = os.path.join(folder_paths.base_path, 'user', 'default', 'workflows')
        if os.path.exists(user_workflows):
            default_dirs.append(user_workflows)

        output_dir = os.path.join(folder_paths.base_path, 'output')
        if os.path.exists(output_dir):
            default_dirs.append(output_dir)

        return web.json_response({
            'success': True,
            'tracked_models': len(used_models_tracking),
            'cache_file': USAGE_CACHE_FILE,
            'cache_size_bytes': cache_size,
            'default_directories': default_dirs
        })
    except Exception as e:
        logging.error(f"[WMD] Cache info error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/check-exists")
async def check_model_exists_endpoint(request):
    """Check if a model exists in a specific directory"""
    try:
        data = await request.json()
        filename = data.get('filename')
        directory = data.get('directory')

        if not filename or not directory:
            return web.json_response({'error': 'Missing filename or directory'}, status=400)

        exists, size = check_model_exists(directory, filename)

        return web.json_response({
            'exists': exists,
            'size': size or ''
        })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Check exists error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/search-url")
async def search_model_url(request):
    """Search for model URL using HuggingFace and CivitAI APIs"""
    try:
        data = await request.json()
        filename = data.get('filename')

        if not filename:
            return web.json_response({'error': 'Missing filename'}, status=400)

        # Search with API calls enabled
        url, source = find_model_url(filename, search_apis=True)

        if url:
            # Extract HuggingFace info if applicable
            hf_repo, hf_path = extract_huggingface_info(url)

            return web.json_response({
                'success': True,
                'url': url,
                'source': source,
                'hf_repo': hf_repo or '',
                'hf_path': hf_path or ''
            })
        else:
            return web.json_response({
                'success': False,
                'message': 'No URL found for this model'
            })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Search URL error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/advanced-search")
async def advanced_search(request):
    """Search for model URL using Tavily API (advanced search)"""
    try:
        data = await request.json()
        filename = data.get('filename')

        if not filename:
            return web.json_response({'error': 'Missing filename'}, status=400)

        # Check if Tavily is configured
        if not get_tavily_api_key():
            return web.json_response({
                'success': False,
                'error': 'Tavily API key not configured'
            }, status=400)

        # Check cache first
        cached = get_cached_metadata(filename)
        if cached and cached.get('url'):
            logging.info(f"[Workflow-Models-Downloader] Using cached result for: {filename}")
            return web.json_response({
                'success': True,
                'url': cached['url'],
                'source': cached.get('source', 'cached'),
                'hf_repo': cached.get('hf_repo', ''),
                'hf_path': cached.get('hf_path', ''),
                'model_name': cached.get('model_name', ''),
                'civitai_url': cached.get('civitai_url', ''),
                'from_cache': True,
                'metadata': cached
            })

        # Search with Tavily
        result = search_tavily_api(filename)

        if result:
            if result.get('url'):
                # Direct URL found
                hf_repo, hf_path = extract_huggingface_info(result['url'])

                # Build metadata to cache
                metadata = {
                    'url': result['url'],
                    'source': result.get('source', 'tavily'),
                    'hf_repo': hf_repo or result.get('repo', ''),
                    'hf_path': hf_path or '',
                    'model_name': result.get('model_name', ''),
                    'civitai_url': result.get('civitai_url', ''),
                    'search_method': 'tavily_advanced'
                }

                # Save to cache
                save_search_metadata(filename, metadata)

                return web.json_response({
                    'success': True,
                    'url': result['url'],
                    'source': result.get('source', 'tavily'),
                    'hf_repo': hf_repo or result.get('repo', ''),
                    'hf_path': hf_path or '',
                    'model_name': result.get('model_name', ''),
                    'civitai_url': result.get('civitai_url', ''),
                    'metadata': metadata
                })
            elif result.get('results'):
                # Return suggestions for user to choose
                suggestions = []
                for r in result['results']:
                    suggestions.append({
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'snippet': r.get('content', '')[:200] if r.get('content') else ''
                    })

                # Cache suggestions too
                metadata = {
                    'suggestions': suggestions,
                    'search_method': 'tavily_suggestions'
                }
                save_search_metadata(filename, metadata)

                return web.json_response({
                    'success': True,
                    'suggestions': suggestions,
                    'message': 'No direct download URL found, but here are some relevant results'
                })

        return web.json_response({
            'success': False,
            'message': 'No results found for this model'
        })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Advanced search error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/search-cache/{filename}")
async def get_search_cache(request):
    """Get cached search metadata for a filename"""
    try:
        filename = request.match_info['filename']
        # URL decode the filename
        filename = urllib.parse.unquote(filename)

        cached = get_cached_metadata(filename)
        if cached:
            return web.json_response({
                'success': True,
                'metadata': cached
            })
        else:
            return web.json_response({
                'success': False,
                'message': 'No cached metadata found'
            })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Get search cache error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/lookup-hash")
async def lookup_by_hash(request):
    """Look up model on CivitAI by calculating file hash"""
    try:
        data = await request.json()
        filename = data.get('filename')
        directory = data.get('directory')

        if not filename or not directory:
            return web.json_response({'error': 'Missing filename or directory'}, status=400)

        # Find the model file
        filepath = find_model_file_path(directory, filename)

        if not filepath:
            return web.json_response({
                'success': False,
                'message': 'Model file not found locally'
            })

        # Calculate hash (this may take time for large files)
        logging.info(f"[Workflow-Models-Downloader] Calculating hash for: {filename}")
        file_hash = calculate_file_hash(filepath)

        if not file_hash:
            return web.json_response({
                'success': False,
                'message': 'Failed to calculate file hash'
            })

        logging.info(f"[Workflow-Models-Downloader] Hash: {file_hash[:16]}... Looking up on CivitAI")

        # Look up on CivitAI
        model_info = lookup_civitai_by_hash(file_hash)

        if model_info and model_info.get('download_url'):
            return web.json_response({
                'success': True,
                'hash': file_hash,
                'model_name': model_info.get('model_name'),
                'model_type': model_info.get('model_type'),
                'version_name': model_info.get('version_name'),
                'original_filename': model_info.get('original_filename'),
                'url': model_info.get('download_url'),
                'model_id': model_info.get('model_id'),
                'civitai_url': f"https://civitai.com/models/{model_info.get('model_id')}" if model_info.get('model_id') else None,
                'source': 'civitai_hash'
            })
        else:
            return web.json_response({
                'success': False,
                'hash': file_hash,
                'message': 'Model not found on CivitAI'
            })

    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Hash lookup error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/download-url")
async def download_from_url(request):
    """Download a model from a direct URL"""
    try:
        data = await request.json()

        url = data.get('url')
        filename = data.get('filename')
        target_dir = data.get('directory')

        if not all([url, filename, target_dir]):
            return web.json_response({'error': 'Missing required fields (url, filename, directory)'}, status=400)

        # Generate download ID
        download_id = f"direct_{filename}".replace('/', '_').replace('\\', '_')

        # Check if already downloading
        with download_lock:
            if download_id in download_progress and download_progress[download_id].get('status') == 'downloading':
                return web.json_response({'error': 'Already downloading'}, status=400)

            download_progress[download_id] = {
                'status': 'starting',
                'progress': 0,
                'filename': filename,
                'total_size': 0,
                'downloaded': 0
            }

        # Start download in background thread
        thread = threading.Thread(
            target=_download_from_url_thread,
            args=(download_id, url, filename, target_dir)
        )
        thread.start()

        return web.json_response({
            'success': True,
            'download_id': download_id,
            'message': f'Started downloading {filename}'
        })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Download URL error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/download")
async def download_model(request):
    """Start downloading a model from HuggingFace"""
    try:
        data = await request.json()

        hf_repo = data.get('hf_repo')
        hf_path = data.get('hf_path')
        filename = data.get('filename')
        target_dir = data.get('directory')
        force = data.get('force', False)  # Force re-download even if exists

        if not all([hf_repo, filename, target_dir]):
            return web.json_response({'error': 'Missing required fields'}, status=400)

        # Generate download ID
        download_id = f"{hf_repo}/{filename}".replace('/', '_')

        # Check if already downloading
        with download_lock:
            if download_id in download_progress and download_progress[download_id].get('status') == 'downloading':
                return web.json_response({'error': 'Already downloading'}, status=400)

            download_progress[download_id] = {
                'status': 'starting',
                'progress': 0,
                'filename': filename,
                'total_size': 0,
                'downloaded': 0
            }

        # Start download in background thread
        thread = threading.Thread(
            target=_download_model_thread,
            args=(download_id, hf_repo, hf_path or filename, filename, target_dir)
        )
        thread.start()

        return web.json_response({
            'success': True,
            'download_id': download_id,
            'message': f'Started downloading {filename}'
        })
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Download start error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/progress/{download_id}")
async def get_download_progress(request):
    """Get download progress for a specific download"""
    download_id = request.match_info['download_id']

    with download_lock:
        if download_id in download_progress:
            return web.json_response(download_progress[download_id])
        else:
            return web.json_response({'error': 'Download not found'}, status=404)


@routes.get("/workflow-models/progress")
async def get_all_progress(request):
    """Get all download progress"""
    with download_lock:
        return web.json_response(dict(download_progress))


@routes.post("/workflow-models/cancel/{download_id}")
async def cancel_download(request):
    """Cancel a download"""
    download_id = request.match_info['download_id']

    with download_lock:
        if download_id in download_progress:
            cancelled_downloads.add(download_id)
            download_progress[download_id]['status'] = 'cancelled'
            logging.info(f"[Workflow-Models-Downloader] Cancelled download: {download_id}")
            return web.json_response({'success': True, 'message': 'Download cancelled'})
        else:
            return web.json_response({'error': 'Download not found'}, status=404)


def _download_model_thread(download_id, hf_repo, hf_path, filename, target_dir):
    """Background thread to download a model"""
    try:
        from huggingface_hub import hf_hub_download
        import requests

        # Normalize path separators for the OS
        target_dir_normalized = target_dir.replace('/', os.sep).replace('\\', os.sep)
        target_path = os.path.join(folder_paths.models_dir, target_dir_normalized)

        # Create directory if it doesn't exist
        try:
            os.makedirs(target_path, exist_ok=True)
            logging.info(f"[Workflow-Models-Downloader] Target directory: {target_path}")
        except Exception as dir_error:
            logging.error(f"[Workflow-Models-Downloader] Failed to create directory {target_path}: {dir_error}")
            raise

        with download_lock:
            download_progress[download_id]['status'] = 'downloading'

        # Get HuggingFace token if available
        hf_token = get_huggingface_token()
        headers = {}
        if hf_token:
            headers['Authorization'] = f'Bearer {hf_token}'

        # Get file size first
        try:
            url = f"https://huggingface.co/{hf_repo}/resolve/main/{hf_path}"
            response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
            total_size = int(response.headers.get('content-length', 0))
            with download_lock:
                download_progress[download_id]['total_size'] = total_size
        except:
            total_size = 0

        # Download with progress callback
        def progress_callback(downloaded, total):
            with download_lock:
                download_progress[download_id]['downloaded'] = downloaded
                download_progress[download_id]['total_size'] = total
                if total > 0:
                    download_progress[download_id]['progress'] = int((downloaded / total) * 100)

        # Use requests for download with progress
        url = f"https://huggingface.co/{hf_repo}/resolve/main/{hf_path}"
        dest_file = os.path.join(target_path, filename)

        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(dest_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                # Check for cancellation
                if download_id in cancelled_downloads:
                    logging.info(f"[Workflow-Models-Downloader] Download cancelled: {filename}")
                    f.close()
                    # Try to delete partial file
                    try:
                        os.remove(dest_file)
                    except:
                        pass
                    cancelled_downloads.discard(download_id)
                    return

                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress_callback(downloaded, total_size)

        with download_lock:
            download_progress[download_id]['status'] = 'completed'
            download_progress[download_id]['progress'] = 100

        # Cache the URL for future use
        hf_url = f"https://huggingface.co/{hf_repo}/resolve/main/{hf_path}"
        _cache_download_url(filename, hf_url, 'huggingface', hf_repo=hf_repo, hf_path=hf_path)

        logging.info(f"[Workflow-Models-Downloader] Downloaded: {filename}")

    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        if e.response is not None:
            status_code = e.response.status_code
            if status_code in [401, 403]:
                if 'huggingface.co' in url:
                    error_msg = f"Unauthorized (HTTP {status_code}): HuggingFace token required. Go to File > Settings > Workflow Models Downloader to configure your HuggingFace token. Get one at https://huggingface.co/settings/tokens"
                else:
                    error_msg = f"Unauthorized (HTTP {status_code}): Authentication required for this model."
            elif status_code == 404:
                error_msg = f"Model not found (HTTP 404): The file may have been moved or deleted."
        logging.error(f"[Workflow-Models-Downloader] Download error: {error_msg}")
        with download_lock:
            download_progress[download_id]['status'] = 'error'
            download_progress[download_id]['error'] = error_msg
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Download error: {e}")
        with download_lock:
            download_progress[download_id]['status'] = 'error'
            download_progress[download_id]['error'] = str(e)
    finally:
        # Clean up cancelled flag
        cancelled_downloads.discard(download_id)


def _download_from_url_thread(download_id, url, filename, target_dir):
    """Background thread to download a model from direct URL"""
    try:
        import requests

        # Normalize path separators for the OS
        target_dir_normalized = target_dir.replace('/', os.sep).replace('\\', os.sep)
        target_path = os.path.join(folder_paths.models_dir, target_dir_normalized)

        # Create directory if it doesn't exist
        try:
            os.makedirs(target_path, exist_ok=True)
            logging.info(f"[Workflow-Models-Downloader] Target directory: {target_path}")
        except Exception as dir_error:
            logging.error(f"[Workflow-Models-Downloader] Failed to create directory {target_path}: {dir_error}")
            raise

        with download_lock:
            download_progress[download_id]['status'] = 'downloading'

        dest_file = os.path.join(target_path, filename)

        # Prepare headers based on URL source
        headers = {}
        if 'civitai.com' in url:
            civitai_key = get_civitai_api_key()
            if civitai_key:
                # CivitAI uses token as query parameter
                if '?' in url:
                    url = f"{url}&token={civitai_key}"
                else:
                    url = f"{url}?token={civitai_key}"
        elif 'huggingface.co' in url:
            hf_token = get_huggingface_token()
            if hf_token:
                headers['Authorization'] = f'Bearer {hf_token}'

        # Download with progress
        response = requests.get(url, stream=True, timeout=30, allow_redirects=True, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with download_lock:
            download_progress[download_id]['total_size'] = total_size

        with open(dest_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                # Check for cancellation
                if download_id in cancelled_downloads:
                    logging.info(f"[Workflow-Models-Downloader] Download cancelled: {filename}")
                    f.close()
                    # Try to delete partial file
                    try:
                        os.remove(dest_file)
                    except:
                        pass
                    cancelled_downloads.discard(download_id)
                    return

                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    with download_lock:
                        download_progress[download_id]['downloaded'] = downloaded
                        if total_size > 0:
                            download_progress[download_id]['progress'] = int((downloaded / total_size) * 100)

        with download_lock:
            download_progress[download_id]['status'] = 'completed'
            download_progress[download_id]['progress'] = 100

        # Cache the URL for future use
        source = 'civitai' if 'civitai.com' in url else ('huggingface' if 'huggingface.co' in url else 'direct')
        hf_repo, hf_path = extract_huggingface_info(url)
        _cache_download_url(filename, url, source, hf_repo=hf_repo, hf_path=hf_path)

        logging.info(f"[Workflow-Models-Downloader] Downloaded from URL: {filename}")

    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        if e.response is not None:
            status_code = e.response.status_code
            if status_code in [401, 403]:
                if 'huggingface.co' in url:
                    error_msg = f"Unauthorized (HTTP {status_code}): HuggingFace token required. Go to File > Settings > Workflow Models Downloader to configure your HuggingFace token. Get one at https://huggingface.co/settings/tokens"
                elif 'civitai.com' in url:
                    error_msg = f"Unauthorized (HTTP {status_code}): CivitAI API key required. Go to File > Settings > Workflow Models Downloader to configure your CivitAI API key."
                else:
                    error_msg = f"Unauthorized (HTTP {status_code}): Authentication required for this model."
            elif status_code == 404:
                error_msg = f"Model not found (HTTP 404): The file may have been moved or deleted."
        logging.error(f"[Workflow-Models-Downloader] URL download error: {error_msg}")
        with download_lock:
            download_progress[download_id]['status'] = 'error'
            download_progress[download_id]['error'] = error_msg
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] URL download error: {e}")
        with download_lock:
            download_progress[download_id]['status'] = 'error'
            download_progress[download_id]['error'] = str(e)
    finally:
        # Clean up cancelled flag
        cancelled_downloads.discard(download_id)


@routes.get("/workflow-models/version")
async def get_version(request):
    """Get extension version"""
    return web.Response(text="1.7.0")


@routes.get("/workflow-models/settings")
async def get_settings(request):
    """Get current settings (with masked tokens)"""
    try:
        settings = load_settings()
        # Return masked versions for display
        masked = {
            'huggingface_token': mask_token(settings.get('huggingface_token', '')),
            'civitai_api_key': mask_token(settings.get('civitai_api_key', '')),
            'tavily_api_key': mask_token(settings.get('tavily_api_key', '')),
            'huggingface_token_set': bool(settings.get('huggingface_token', '')),
            'civitai_api_key_set': bool(settings.get('civitai_api_key', '')),
            'tavily_api_key_set': bool(settings.get('tavily_api_key', '')),
            'enable_advanced_search': settings.get('enable_advanced_search', False)
        }
        return web.json_response(masked)
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Get settings error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/settings")
async def update_settings(request):
    """Update settings"""
    try:
        data = await request.json()
        current = load_settings()

        # Only update if new value is provided (not empty or masked)
        if 'huggingface_token' in data:
            token = data['huggingface_token']
            if token and not token.startswith('***'):
                current['huggingface_token'] = token
            elif token == '':
                current['huggingface_token'] = ''

        if 'civitai_api_key' in data:
            key = data['civitai_api_key']
            if key and not key.startswith('***'):
                current['civitai_api_key'] = key
            elif key == '':
                current['civitai_api_key'] = ''

        if 'tavily_api_key' in data:
            key = data['tavily_api_key']
            if key and not key.startswith('***'):
                current['tavily_api_key'] = key
            elif key == '':
                current['tavily_api_key'] = ''

        if 'enable_advanced_search' in data:
            current['enable_advanced_search'] = bool(data['enable_advanced_search'])

        if save_settings(current):
            return web.json_response({'success': True})
        else:
            return web.json_response({'error': 'Failed to save settings'}, status=500)
    except Exception as e:
        logging.error(f"[Workflow-Models-Downloader] Update settings error: {e}")
        return web.json_response({'error': str(e)}, status=500)


def mask_token(token):
    """Mask a token for display, showing only first 4 and last 4 characters"""
    if not token:
        return ''
    if len(token) <= 8:
        return '*' * len(token)
    return token[:4] + '*' * (len(token) - 8) + token[-4:]


# ============================================================================
# Model Browser Endpoints
# ============================================================================

def format_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


@routes.get("/workflow-models/installed")
async def get_installed_models(request):
    """Get all installed models with metadata"""
    try:
        models = []

        # Valid model file extensions
        MODEL_EXTENSIONS = {'.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf', '.sft'}

        # Known model folder types (curated list)
        model_types = set([
            'checkpoints', 'loras', 'vae', 'controlnet', 'clip', 'clip_vision',
            'text_encoders', 'diffusion_models', 'unet', 'embeddings',
            'upscale_models', 'hypernetworks', 'gligen', 'style_models',
            'ipadapter', 'instantid', 'photomaker', 'pulid', 'sams',
            'depthanything', 'groundingdino', 'insightface', 'animatediff_models',
            'vae_approx', 'ultralytics', 'mmdets', 'onnx', 'reactor', 'facerestore_models',
            'facedetection', 'liveportrait', 'layerstyle', 'rembg', 'segment_anything',
            'inpaint', 'prompt_expansion', 'xlabs', 'LLM', 'Joy_caption', 'Florence2',
            'llm_gguf', 'CogVideo', 'TIPO', 'blip', 'nsfw_detector', 'mediapipe'
        ])

        # Folders to exclude (not model folders)
        EXCLUDED_FOLDERS = {
            'custom_nodes', 'configs', 'fonts', 'kjnodes_fonts', 'web', 'js',
            'user', 'input', 'output', 'temp', 'models', 'pycache'
        }

        # Add custom folder types from folder_paths, but only if they look like model folders
        if hasattr(folder_paths, 'folder_names_and_paths'):
            for folder_type in folder_paths.folder_names_and_paths.keys():
                # Skip excluded folders
                if folder_type.lower() in EXCLUDED_FOLDERS:
                    continue
                # Skip if folder name contains certain patterns
                if any(x in folder_type.lower() for x in ['pycache', '_cache', 'config', 'font']):
                    continue
                model_types.add(folder_type)

        for folder_type in model_types:
            try:
                files = folder_paths.get_filename_list(folder_type)

                for filename in files:
                    try:
                        # Only include files with model extensions
                        ext = os.path.splitext(filename)[1].lower()
                        if ext not in MODEL_EXTENSIONS:
                            continue

                        full_path = folder_paths.get_full_path(folder_type, filename)
                        if full_path and os.path.exists(full_path):
                            stat = os.stat(full_path)
                            models.append({
                                'filename': filename,
                                'type': folder_type,
                                'path': full_path,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'size_human': format_size(stat.st_size)
                            })
                    except Exception as e:
                        logging.debug(f"[WMD] Error processing {filename}: {e}")
                        continue
            except Exception as e:
                logging.debug(f"[WMD] Error scanning {folder_type}: {e}")
                continue

        return web.json_response({'models': models})
    except Exception as e:
        logging.error(f"[WMD] Error getting installed models: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/model/metadata")
async def get_model_metadata(request):
    """Get detailed metadata for a model file"""
    try:
        path = request.query.get('path', '')
        if not path:
            return web.json_response({'error': 'Path is required'}, status=400)

        if not os.path.exists(path):
            return web.json_response({'error': 'File not found'}, status=404)

        # Security check - ensure path is within models directories
        models_dir = folder_paths.models_dir
        if not os.path.abspath(path).startswith(os.path.abspath(models_dir)):
            # Also check extra_model_paths
            valid_path = False
            for folder_type in ['checkpoints', 'loras', 'vae', 'controlnet']:
                try:
                    for base_path in folder_paths.get_folder_paths(folder_type):
                        if os.path.abspath(path).startswith(os.path.abspath(base_path)):
                            valid_path = True
                            break
                except:
                    pass
                if valid_path:
                    break

            if not valid_path:
                return web.json_response({'error': 'Access denied'}, status=403)

        stat = os.stat(path)
        filename = os.path.basename(path)

        # Determine model type from directory structure
        model_type = 'unknown'
        for folder_type in ['checkpoints', 'loras', 'vae', 'controlnet', 'clip', 'embeddings', 'upscale_models']:
            try:
                for base_path in folder_paths.get_folder_paths(folder_type):
                    if path.startswith(base_path):
                        model_type = folder_type
                        break
            except:
                pass

        metadata = {
            'filename': filename,
            'path': path,
            'type': model_type,
            'size': stat.st_size,
            'size_human': format_size(stat.st_size),
            'modified': stat.st_mtime,
            'hash': None  # Optional: compute hash on request
        }

        return web.json_response(metadata)
    except Exception as e:
        logging.error(f"[WMD] Error getting model metadata: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/model/delete")
async def delete_model(request):
    """Delete a model file"""
    try:
        data = await request.json()
        path = data.get('path', '')

        if not path:
            return web.json_response({'error': 'Path is required'}, status=400)

        if not os.path.exists(path):
            return web.json_response({'error': 'File not found'}, status=404)

        # Security check - ensure path is within models directories
        models_dir = folder_paths.models_dir
        valid_path = os.path.abspath(path).startswith(os.path.abspath(models_dir))

        if not valid_path:
            # Also check extra_model_paths
            for folder_type in ['checkpoints', 'loras', 'vae', 'controlnet', 'clip', 'embeddings', 'upscale_models']:
                try:
                    for base_path in folder_paths.get_folder_paths(folder_type):
                        if os.path.abspath(path).startswith(os.path.abspath(base_path)):
                            valid_path = True
                            break
                except:
                    pass
                if valid_path:
                    break

        if not valid_path:
            return web.json_response({'error': 'Access denied - path not in models directory'}, status=403)

        # Ensure it's a file, not a directory
        if not os.path.isfile(path):
            return web.json_response({'error': 'Path is not a file'}, status=400)

        # Delete the file
        os.remove(path)
        logging.info(f"[WMD] Deleted model: {path}")

        return web.json_response({'success': True})
    except Exception as e:
        logging.error(f"[WMD] Error deleting model: {e}")
        return web.json_response({'error': str(e)}, status=500)


# ============================================================================
# Fuzzy Matching System
# ============================================================================

def load_model_aliases():
    """Load model aliases from model-aliases.json"""
    try:
        if os.path.exists(MODEL_ALIASES_FILE):
            with open(MODEL_ALIASES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"[WMD] Error loading model aliases: {e}")

    # Default aliases structure
    return {
        "aliases": {},
        "patterns": [
            {"pattern": r"(.+)[-_]?fp16\.safetensors$", "base": "$1.safetensors"},
            {"pattern": r"(.+)[-_]?fp8\.safetensors$", "base": "$1.safetensors"},
            {"pattern": r"(.+)[-_]?bf16\.safetensors$", "base": "$1.safetensors"},
            {"pattern": r"(.+)[-_]?q8_0\.safetensors$", "base": "$1.safetensors"},
            {"pattern": r"(.+)[-_]?pruned\.safetensors$", "base": "$1.safetensors"},
            {"pattern": r"(.+)[-_]?ema\.safetensors$", "base": "$1.safetensors"}
        ]
    }


def resolve_model_alias(filename):
    """Check if filename is an alias for a known model and return canonical name"""
    aliases_data = load_model_aliases()
    filename_lower = filename.lower()

    # Direct alias lookup
    for canonical, alias_list in aliases_data.get('aliases', {}).items():
        if filename_lower in [a.lower() for a in alias_list]:
            return canonical

    # Pattern matching (for quantization variants)
    for pattern_def in aliases_data.get('patterns', []):
        match = re.match(pattern_def['pattern'], filename, re.IGNORECASE)
        if match:
            base = pattern_def['base'].replace('$1', match.group(1))
            return base

    return filename  # No alias found


def fuzzy_match_model(filename, threshold=0.70):
    """Find similar models with confidence scores"""
    matches = []
    base_name = os.path.splitext(filename)[0].lower()

    # First, check if this is an alias
    canonical = resolve_model_alias(filename)
    if canonical != filename:
        # Found via alias - this is a 100% match for the canonical name
        matches.append({
            'matched_name': canonical,
            'confidence': 100,
            'match_type': 'alias',
            'url': None  # Will be looked up separately
        })

    # Search in model-list.json
    model_list = load_model_list()
    for model in model_list:
        model_filename = model.get('filename', '')
        model_base = os.path.splitext(model_filename)[0].lower()

        # Exact match
        if model_base == base_name:
            matches.append({
                'filename': model_filename,
                'url': model.get('url', ''),
                'confidence': 100,
                'match_type': 'exact',
                'source': 'model_list'
            })
            continue

        # Fuzzy match using SequenceMatcher
        ratio = SequenceMatcher(None, base_name, model_base).ratio()
        if ratio >= threshold:
            matches.append({
                'filename': model_filename,
                'url': model.get('url', ''),
                'confidence': int(ratio * 100),
                'match_type': 'fuzzy',
                'source': 'model_list'
            })

    # Search in popular-models.json
    popular_models = load_popular_models()
    for model_name, model_info in popular_models.items():
        model_base = os.path.splitext(model_name)[0].lower()

        # Exact match
        if model_base == base_name:
            matches.append({
                'filename': model_name,
                'url': model_info.get('url', ''),
                'confidence': 100,
                'match_type': 'exact',
                'source': 'popular_models'
            })
            continue

        # Fuzzy match
        ratio = SequenceMatcher(None, base_name, model_base).ratio()
        if ratio >= threshold:
            matches.append({
                'filename': model_name,
                'url': model_info.get('url', ''),
                'confidence': int(ratio * 100),
                'match_type': 'fuzzy',
                'source': 'popular_models'
            })

    # Search in search_cache.json for previously found models
    search_cache = load_search_cache()
    for cached_name, cached_info in search_cache.items():
        cached_base = os.path.splitext(cached_name)[0].lower()

        # Exact match
        if cached_base == base_name:
            matches.append({
                'filename': cached_name,
                'url': cached_info.get('url', ''),
                'confidence': 100,
                'match_type': 'exact',
                'source': 'search_cache'
            })
            continue

        # Fuzzy match
        ratio = SequenceMatcher(None, base_name, cached_base).ratio()
        if ratio >= threshold:
            matches.append({
                'filename': cached_name,
                'url': cached_info.get('url', ''),
                'confidence': int(ratio * 100),
                'match_type': 'fuzzy',
                'source': 'search_cache'
            })

    # Remove duplicates (keep highest confidence)
    seen = {}
    for match in matches:
        key = match.get('filename', match.get('matched_name', ''))
        if key not in seen or match['confidence'] > seen[key]['confidence']:
            seen[key] = match

    # Sort by confidence descending
    unique_matches = list(seen.values())
    unique_matches.sort(key=lambda x: x['confidence'], reverse=True)

    return unique_matches[:5]  # Top 5 matches


@routes.post("/workflow-models/fuzzy-match")
async def fuzzy_match_endpoint(request):
    """Find similar models using fuzzy matching"""
    try:
        data = await request.json()
        filename = data.get('filename')
        threshold = data.get('threshold', 0.70)

        if not filename:
            return web.json_response({'error': 'Missing filename'}, status=400)

        matches = fuzzy_match_model(filename, threshold)

        return web.json_response({
            'success': True,
            'filename': filename,
            'matches': matches
        })
    except Exception as e:
        logging.error(f"[WMD] Fuzzy match error: {e}")
        return web.json_response({'error': str(e)}, status=500)


# ============================================================================
# URL Analysis for Raw Downloads
# ============================================================================

def guess_model_type_from_filename(filename, url_path=''):
    """Guess the model type and directory from filename and URL path"""
    filename_lower = filename.lower()
    url_path_lower = url_path.lower() if url_path else ''

    # Combine filename and URL path for checking
    # URL path often contains folder hints like /loras/, /vae/, /diffusion_models/
    check_text = filename_lower + ' ' + url_path_lower

    # Check for specific patterns (order matters - more specific first)
    if any(x in check_text for x in ['/loras/', '/lora/', '_lora', '-lora', 'lora_']):
        return 'lora', 'loras'
    elif any(x in check_text for x in ['/vae/', '_vae', '-vae', 'vae_']):
        return 'VAE', 'vae'
    elif any(x in check_text for x in ['/controlnet/', 'controlnet', 'control_v', 'control-']):
        return 'ControlNet', 'controlnet'
    elif any(x in check_text for x in ['/clip/', '/text_encoder/', 'clip_', 'text_encoder']):
        return 'CLIP', 'text_encoders'
    elif any(x in check_text for x in ['/diffusion_model/', '/diffusion_models/', '/unet/', 'unet_', 'diffusion_model']):
        return 'diffusion_model', 'diffusion_models'
    elif any(x in check_text for x in ['/upscale/', 'upscale', 'esrgan', 'realesrgan', '4x_', '2x_']):
        return 'Upscaler', 'upscale_models'
    elif any(x in check_text for x in ['/embedding/', 'embedding_', '.pt']):
        return 'Embedding', 'embeddings'
    elif any(x in check_text for x in ['/ipadapter/', 'ipadapter', 'ip_adapter', 'ip-adapter']):
        return 'IPAdapter', 'ipadapter'
    elif any(x in check_text for x in ['/inpaint/', 'inpaint']):
        return 'Inpaint', 'inpaint'
    elif any(x in check_text for x in ['/checkpoint/', '/checkpoints/']):
        return 'Checkpoint', 'checkpoints'
    elif filename_lower.endswith('.safetensors') or filename_lower.endswith('.ckpt'):
        # Default to checkpoint for .safetensors/.ckpt files
        return 'Checkpoint', 'checkpoints'
    else:
        return 'Unknown', 'checkpoints'


@routes.post("/workflow-models/analyze-url")
async def analyze_url_endpoint(request):
    """Analyze a URL to determine filename, model type, and suggested directory"""
    import requests

    try:
        data = await request.json()
        url = data.get('url', '').strip()

        if not url:
            return web.json_response({'error': 'Missing URL'}, status=400)

        filename = None
        size = None
        source = 'Direct URL'

        # Determine source and extract info
        if 'huggingface.co' in url:
            source = 'HuggingFace'
            # Extract filename from HF URL
            # Format: huggingface.co/repo/model/resolve/main/path/to/file.safetensors
            hf_match = re.search(r'huggingface\.co/([^/]+/[^/]+)(?:/resolve/[^/]+)?/(.+?)(?:\?|$)', url)
            if hf_match:
                path = hf_match.group(2)
                filename = path.split('/')[-1]
                # Clean up query params from filename
                if '?' in filename:
                    filename = filename.split('?')[0]

        elif 'civitai.com' in url:
            source = 'CivitAI'
            # CivitAI URLs are complex - try to get info from API or headers
            # For now, we'll get filename from Content-Disposition header

        # If we don't have a filename yet, try HEAD request
        if not filename:
            try:
                headers = {}
                if 'huggingface.co' in url:
                    hf_token = get_huggingface_token()
                    if hf_token:
                        headers['Authorization'] = f'Bearer {hf_token}'
                elif 'civitai.com' in url:
                    civitai_key = get_civitai_api_key()
                    if civitai_key:
                        if '?' in url:
                            url = f"{url}&token={civitai_key}"
                        else:
                            url = f"{url}?token={civitai_key}"

                response = requests.head(url, headers=headers, allow_redirects=True, timeout=15)

                # Try Content-Disposition header
                cd = response.headers.get('Content-Disposition', '')
                if 'filename=' in cd:
                    # Parse filename from header
                    match = re.search(r'filename[*]?=["\']?([^"\';\n]+)', cd)
                    if match:
                        filename = match.group(1).strip()
                        # Handle UTF-8 encoded filenames
                        if filename.startswith("UTF-8''"):
                            filename = urllib.parse.unquote(filename[7:])

                # Get size from Content-Length
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size_bytes = int(content_length)
                    size_mb = size_bytes / (1024 * 1024)
                    if size_mb >= 1024:
                        size = f"{size_mb/1024:.2f} GB"
                    else:
                        size = f"{size_mb:.1f} MB"

            except Exception as e:
                logging.warning(f"[WMD] Could not fetch URL headers: {e}")

        # If still no filename, extract from URL path
        if not filename:
            parsed = urllib.parse.urlparse(url)
            path = urllib.parse.unquote(parsed.path)
            filename = path.split('/')[-1]
            # Remove query params
            if '?' in filename:
                filename = filename.split('?')[0]

        # If filename is empty or just an extension, generate a name
        if not filename or filename.startswith('.'):
            filename = f"model_{int(asyncio.get_event_loop().time())}.safetensors"

        # Get URL path for type detection (includes folder structure hints)
        parsed_url = urllib.parse.urlparse(url)
        url_path = urllib.parse.unquote(parsed_url.path)

        # Guess model type and directory from both filename AND URL path
        model_type, suggested_dir = guess_model_type_from_filename(filename, url_path)

        return web.json_response({
            'success': True,
            'url': url,
            'filename': filename,
            'model_type': model_type,
            'suggested_directory': suggested_dir,
            'size': size,
            'source': source
        })

    except Exception as e:
        logging.error(f"[WMD] Analyze URL error: {e}")
        return web.json_response({'error': str(e)}, status=500)


# ============================================================================
# aria2 Integration with Resume Support
# ============================================================================

def check_aria2_available():
    """Check if aria2c is installed and available"""
    try:
        aria2_path = shutil.which('aria2c')
        if aria2_path:
            result = subprocess.run([aria2_path, '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
    except Exception:
        pass
    return False


def _download_with_aria2(url, dest_path, download_id, headers=None):
    """Download using aria2c with resume support"""
    global active_download_count

    try:
        aria2_path = shutil.which('aria2c')
        if not aria2_path:
            return False, "aria2c not found"

        dest_dir = os.path.dirname(dest_path)
        dest_file = os.path.basename(dest_path)

        cmd = [
            aria2_path,
            '--dir=' + dest_dir,
            '--out=' + dest_file,
            '--continue=true',           # Resume support
            '--max-connection-per-server=4',
            '--split=4',
            '--min-split-size=1M',
            '--file-allocation=none',
            '--console-log-level=error',
            '--summary-interval=1',
            url
        ]

        if headers:
            for key, value in headers.items():
                cmd.append(f'--header={key}: {value}')

        with download_lock:
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['method'] = 'aria2'

        # Run aria2c process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Monitor process
        while True:
            # Check for cancellation
            if download_id in cancelled_downloads:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()
                return False, "Cancelled"

            # Check if process completed
            poll = process.poll()
            if poll is not None:
                break

            # Try to read progress (aria2c outputs progress to stderr)
            try:
                import time
                time.sleep(0.5)

                # Check file size for progress
                if os.path.exists(dest_path):
                    current_size = os.path.getsize(dest_path)
                    with download_lock:
                        download_progress[download_id]['downloaded'] = current_size
                        total = download_progress[download_id].get('total_size', 0)
                        if total > 0:
                            download_progress[download_id]['progress'] = int((current_size / total) * 100)
            except:
                pass

        # Check result
        if process.returncode == 0:
            with download_lock:
                download_progress[download_id]['status'] = 'completed'
                download_progress[download_id]['progress'] = 100
            return True, None
        else:
            stderr = process.stderr.read() if process.stderr else 'Unknown error'
            return False, stderr

    except Exception as e:
        return False, str(e)
    finally:
        with download_queue_lock:
            active_download_count = max(0, active_download_count - 1)


def _download_native_with_resume(url, dest_path, download_id, headers=None):
    """Download using requests with resume support (.partial file tracking)"""
    import requests
    global active_download_count

    partial_path = dest_path + '.partial'
    resume_byte = 0

    # Check for existing partial download
    if os.path.exists(partial_path):
        resume_byte = os.path.getsize(partial_path)
        logging.info(f"[WMD] Resuming download from byte {resume_byte}")

    req_headers = headers.copy() if headers else {}
    if resume_byte > 0:
        req_headers['Range'] = f'bytes={resume_byte}-'

    try:
        response = requests.get(url, stream=True, timeout=30, allow_redirects=True, headers=req_headers)

        # Check if server supports resume
        if resume_byte > 0 and response.status_code != 206:
            # Server doesn't support resume, start from beginning
            resume_byte = 0
            response = requests.get(url, stream=True, timeout=30, allow_redirects=True, headers=headers or {})

        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        if resume_byte > 0:
            total_size += resume_byte  # Add already downloaded bytes

        with download_lock:
            download_progress[download_id]['total_size'] = total_size
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['method'] = 'native_resume'

        # Open file in append mode if resuming
        mode = 'ab' if resume_byte > 0 else 'wb'
        downloaded = resume_byte

        with open(partial_path, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                # Check for cancellation
                if download_id in cancelled_downloads:
                    return False, "Cancelled"

                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    with download_lock:
                        download_progress[download_id]['downloaded'] = downloaded
                        if total_size > 0:
                            download_progress[download_id]['progress'] = int((downloaded / total_size) * 100)

        # Rename partial to final
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(partial_path, dest_path)

        with download_lock:
            download_progress[download_id]['status'] = 'completed'
            download_progress[download_id]['progress'] = 100

        return True, None

    except Exception as e:
        # Keep partial file for resume
        return False, str(e)
    finally:
        with download_queue_lock:
            active_download_count = max(0, active_download_count - 1)


# ============================================================================
# Download Queue System
# ============================================================================

download_queue_worker_running = False


def start_download_queue_worker():
    """Start the background download queue worker if not already running"""
    global download_queue_worker_running

    if download_queue_worker_running:
        return

    download_queue_worker_running = True
    worker_thread = threading.Thread(target=_download_queue_worker, daemon=True)
    worker_thread.start()
    logging.info("[WMD] Download queue worker started")


def _download_queue_worker():
    """Background thread that processes download queue"""
    global download_queue_worker_running, active_download_count
    import time

    while download_queue_worker_running:
        try:
            with download_queue_lock:
                # Check if we can start a new download
                current_max = max_parallel_downloads
                if current_max == 0:  # 0 means unlimited
                    can_start = len(download_queue) > 0
                else:
                    can_start = active_download_count < current_max and len(download_queue) > 0

                if can_start:
                    next_download = download_queue.pop(0)
                    active_download_count += 1

                    # Start download in separate thread
                    thread = threading.Thread(
                        target=_process_queued_download,
                        args=(next_download,),
                        daemon=True
                    )
                    thread.start()
        except Exception as e:
            logging.error(f"[WMD] Queue worker error: {e}")

        time.sleep(0.5)


def _process_queued_download(download_info):
    """Process a download from the queue"""
    global active_download_count

    download_id = download_info['download_id']
    url = download_info['url']
    dest_path = download_info['dest_path']
    headers = download_info.get('headers', {})
    filename = download_info.get('filename', '')

    try:
        with download_lock:
            download_progress[download_id] = {
                'status': 'starting',
                'progress': 0,
                'filename': filename,
                'total_size': 0,
                'downloaded': 0,
                'queued': False
            }

        # Try aria2 first if available
        aria2_available = check_aria2_available()

        if aria2_available:
            success, error = _download_with_aria2(url, dest_path, download_id, headers)
        else:
            success, error = _download_native_with_resume(url, dest_path, download_id, headers)

        if not success and error != "Cancelled":
            with download_lock:
                download_progress[download_id]['status'] = 'error'
                download_progress[download_id]['error'] = error

        # Cache URL on success
        if success:
            source = 'civitai' if 'civitai.com' in url else ('huggingface' if 'huggingface.co' in url else 'direct')
            hf_repo, hf_path = extract_huggingface_info(url)
            _cache_download_url(filename, url, source, hf_repo=hf_repo, hf_path=hf_path)
            logging.info(f"[WMD] Download completed: {filename}")

    except Exception as e:
        logging.error(f"[WMD] Queued download error: {e}")
        with download_lock:
            download_progress[download_id]['status'] = 'error'
            download_progress[download_id]['error'] = str(e)
    finally:
        with download_queue_lock:
            active_download_count = max(0, active_download_count - 1)
        cancelled_downloads.discard(download_id)


@routes.post("/workflow-models/queue-download")
async def queue_download_endpoint(request):
    """Add a download to the queue"""
    try:
        data = await request.json()

        url = data.get('url')
        filename = data.get('filename')
        target_dir = data.get('directory')

        if not all([url, filename, target_dir]):
            return web.json_response({'error': 'Missing required fields'}, status=400)

        # Generate download ID
        download_id = f"queued_{filename}_{int(asyncio.get_event_loop().time() * 1000)}".replace('/', '_').replace('\\', '_')

        # Prepare headers
        headers = {}
        if 'civitai.com' in url:
            civitai_key = get_civitai_api_key()
            if civitai_key:
                if '?' in url:
                    url = f"{url}&token={civitai_key}"
                else:
                    url = f"{url}?token={civitai_key}"
        elif 'huggingface.co' in url:
            hf_token = get_huggingface_token()
            if hf_token:
                headers['Authorization'] = f'Bearer {hf_token}'

        # Normalize path
        target_dir_normalized = target_dir.replace('/', os.sep).replace('\\', os.sep)
        dest_path = os.path.join(folder_paths.models_dir, target_dir_normalized, filename)

        # Create directory
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Add to queue
        download_info = {
            'download_id': download_id,
            'url': url,
            'dest_path': dest_path,
            'filename': filename,
            'headers': headers
        }

        with download_queue_lock:
            download_queue.append(download_info)

        # Initialize progress tracking
        with download_lock:
            download_progress[download_id] = {
                'status': 'queued',
                'progress': 0,
                'filename': filename,
                'total_size': 0,
                'downloaded': 0,
                'queued': True
            }

        # Ensure queue worker is running
        start_download_queue_worker()

        return web.json_response({
            'success': True,
            'download_id': download_id,
            'queued': True,
            'message': f'Added {filename} to download queue'
        })

    except Exception as e:
        logging.error(f"[WMD] Queue download error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.get("/workflow-models/queue-status")
async def get_queue_status(request):
    """Get download queue status"""
    try:
        with download_queue_lock:
            queue_count = len(download_queue)
            active = active_download_count

        return web.json_response({
            'queued': queue_count,
            'active': active,
            'max_parallel': max_parallel_downloads,
            'aria2_available': check_aria2_available()
        })
    except Exception as e:
        logging.error(f"[WMD] Queue status error: {e}")
        return web.json_response({'error': str(e)}, status=500)


@routes.post("/workflow-models/settings/parallel")
async def set_parallel_downloads(request):
    """Set max parallel downloads"""
    global max_parallel_downloads

    try:
        data = await request.json()
        value = data.get('max_parallel', 3)

        # Validate value
        if not isinstance(value, int) or value < 0 or value > 50:
            return web.json_response({'error': 'Invalid value (must be 0-50)'}, status=400)

        max_parallel_downloads = value

        # Save to settings
        settings = load_settings()
        settings['max_parallel_downloads'] = value
        save_settings(settings)

        logging.info(f"[WMD] Max parallel downloads set to: {value}")

        return web.json_response({
            'success': True,
            'max_parallel': value
        })
    except Exception as e:
        logging.error(f"[WMD] Set parallel downloads error: {e}")
        return web.json_response({'error': str(e)}, status=500)


# Initialize max_parallel from settings on load
def _init_parallel_setting():
    global max_parallel_downloads
    settings = load_settings()
    max_parallel_downloads = settings.get('max_parallel_downloads', 3)

_init_parallel_setting()


logging.info("[Workflow-Models-Downloader] Extension loaded successfully")
