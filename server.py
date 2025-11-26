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

# Download progress tracking
download_progress = {}
download_lock = threading.Lock()
cancelled_downloads = set()  # Track cancelled download IDs

# Settings cache
_settings_cache = None


def load_settings():
    """Load settings from settings.json"""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    default_settings = {
        'huggingface_token': '',
        'civitai_api_key': ''
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
    """Find the full path to a model file"""
    models_dir = folder_paths.models_dir

    dirs_to_check = [target_dir]
    if target_dir in EQUIVALENT_DIRECTORIES:
        dirs_to_check = EQUIVALENT_DIRECTORIES[target_dir]

    for check_dir in dirs_to_check:
        # Check exact path
        model_path = os.path.join(models_dir, check_dir, filename)
        if os.path.exists(model_path):
            return model_path

        # Search subdirectories
        base_dir = os.path.join(models_dir, check_dir)
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
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


def check_model_exists(target_dir, filename):
    """Check if model file exists in target directory, equivalent directories, or subdirectories"""
    models_dir = folder_paths.models_dir

    # Get list of directories to check (including equivalent ones)
    dirs_to_check = [target_dir]
    if target_dir in EQUIVALENT_DIRECTORIES:
        dirs_to_check = EQUIVALENT_DIRECTORIES[target_dir]

    for check_dir in dirs_to_check:
        # Check exact path
        model_path = os.path.join(models_dir, check_dir, filename)
        if os.path.exists(model_path):
            try:
                size_bytes = os.path.getsize(model_path)
                size_mb = size_bytes / (1024 * 1024)
                if size_mb >= 1024:
                    return True, f"{size_mb/1024:.2f} GB"
                else:
                    return True, f"{size_mb:.1f} MB"
            except:
                return True, None

        # Search in subdirectories (common for loras, checkpoints, etc.)
        base_dir = os.path.join(models_dir, check_dir)
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                if filename in files:
                    try:
                        found_path = os.path.join(root, filename)
                        size_bytes = os.path.getsize(found_path)
                        size_mb = size_bytes / (1024 * 1024)
                        if size_mb >= 1024:
                            return True, f"{size_mb/1024:.2f} GB"
                        else:
                            return True, f"{size_mb:.1f} MB"
                    except:
                        return True, None

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

        # If no URL found, try to find one from our registries (not API search - that's manual)
        url_source = None
        if not url:
            found_url, url_source = find_model_url(model, search_apis=False)
            if found_url:
                url = found_url

        # Extract HuggingFace info
        hf_repo, hf_path = extract_huggingface_info(url)

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
            'url_source': url_source or ('workflow' if url else None)
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

        logging.info(f"[Workflow-Models-Downloader] Downloaded: {filename}")

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

        logging.info(f"[Workflow-Models-Downloader] Downloaded from URL: {filename}")

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
    return web.Response(text="1.5.0")


@routes.get("/workflow-models/settings")
async def get_settings(request):
    """Get current settings (with masked tokens)"""
    try:
        settings = load_settings()
        # Return masked versions for display
        masked = {
            'huggingface_token': mask_token(settings.get('huggingface_token', '')),
            'civitai_api_key': mask_token(settings.get('civitai_api_key', '')),
            'huggingface_token_set': bool(settings.get('huggingface_token', '')),
            'civitai_api_key_set': bool(settings.get('civitai_api_key', ''))
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


logging.info("[Workflow-Models-Downloader] Extension loaded successfully")
