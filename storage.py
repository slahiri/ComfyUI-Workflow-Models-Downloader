"""
Storage Module: Unified data access layer

Provides backward-compatible functions that use SQLite repositories internally.
This module replaces direct JSON file operations in server.py.
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .database import get_db
from .repositories import (
    SettingsRepository,
    DownloadHistoryRepository,
    ModelMetadataRepository,
    ModelCatalogRepository,
    SearchCacheRepository,
    UsageCacheRepository,
    NodeMetadataRepository,
    ModelAliasRepository
)

# Extension path
EXTENSION_PATH = os.path.dirname(__file__)

# Initialize repositories (lazy loading)
_settings_repo = None
_download_history_repo = None
_model_metadata_repo = None
_model_catalog_repo = None
_search_cache_repo = None
_usage_cache_repo = None
_node_metadata_repo = None
_model_alias_repo = None


def _get_settings_repo():
    global _settings_repo
    if _settings_repo is None:
        _settings_repo = SettingsRepository()
    return _settings_repo


def _get_download_history_repo():
    global _download_history_repo
    if _download_history_repo is None:
        _download_history_repo = DownloadHistoryRepository()
    return _download_history_repo


def _get_model_metadata_repo():
    global _model_metadata_repo
    if _model_metadata_repo is None:
        _model_metadata_repo = ModelMetadataRepository()
    return _model_metadata_repo


def _get_model_catalog_repo():
    global _model_catalog_repo
    if _model_catalog_repo is None:
        _model_catalog_repo = ModelCatalogRepository()
    return _model_catalog_repo


def _get_search_cache_repo():
    global _search_cache_repo
    if _search_cache_repo is None:
        _search_cache_repo = SearchCacheRepository()
    return _search_cache_repo


def _get_usage_cache_repo():
    global _usage_cache_repo
    if _usage_cache_repo is None:
        _usage_cache_repo = UsageCacheRepository()
    return _usage_cache_repo


def _get_node_metadata_repo():
    global _node_metadata_repo
    if _node_metadata_repo is None:
        _node_metadata_repo = NodeMetadataRepository()
    return _node_metadata_repo


def _get_model_alias_repo():
    global _model_alias_repo
    if _model_alias_repo is None:
        _model_alias_repo = ModelAliasRepository()
    return _model_alias_repo


# =============================================================================
# SETTINGS FUNCTIONS (replaces settings.json operations)
# =============================================================================

_settings_cache = None

def load_settings() -> Dict[str, Any]:
    """Load settings from database or fallback to ComfyUI settings"""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    default_settings = {
        'huggingface_token': '',
        'civitai_api_key': '',
        'tavily_api_key': '',
        'enable_advanced_search': False,
        'max_parallel_downloads': 3
    }

    try:
        repo = _get_settings_repo()
        db_settings = repo.get_all()
        if db_settings:
            _settings_cache = {**default_settings, **db_settings}
            return _settings_cache
    except Exception as e:
        logging.debug(f"[WMD] Error loading settings from DB: {e}")

    # Fall back to ComfyUI's native settings
    try:
        import folder_paths
        comfy_settings_path = os.path.join(folder_paths.base_path, 'user', 'default', 'comfy.settings.json')
        if os.path.exists(comfy_settings_path):
            with open(comfy_settings_path, 'r', encoding='utf-8') as f:
                comfy_settings = json.load(f)
                _settings_cache = {
                    'huggingface_token': comfy_settings.get('WorkflowModelsDownloader.HuggingFaceToken', ''),
                    'civitai_api_key': comfy_settings.get('WorkflowModelsDownloader.CivitAIApiKey', ''),
                    'tavily_api_key': comfy_settings.get('WorkflowModelsDownloader.TavilyApiKey', ''),
                    'enable_advanced_search': comfy_settings.get('WorkflowModelsDownloader.EnableAdvancedSearch', False),
                    'max_parallel_downloads': comfy_settings.get('WorkflowModelsDownloader.MaxParallelDownloads', 3)
                }
                return _settings_cache
    except Exception as e:
        logging.debug(f"[WMD] Error loading ComfyUI settings: {e}")

    _settings_cache = default_settings
    return _settings_cache


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to database"""
    global _settings_cache
    try:
        repo = _get_settings_repo()
        for key, value in settings.items():
            repo.set(key, value)
        _settings_cache = settings
        logging.info("[WMD] Settings saved to database")
        return True
    except Exception as e:
        logging.error(f"[WMD] Error saving settings: {e}")
        return False


def clear_settings_cache():
    """Clear the settings cache to force reload"""
    global _settings_cache
    _settings_cache = None


# =============================================================================
# DOWNLOAD HISTORY FUNCTIONS (replaces download_history.json operations)
# =============================================================================

# In-memory cache for backward compatibility
_download_history = []


def load_download_history() -> List[Dict]:
    """Load download history from database"""
    global _download_history
    try:
        repo = _get_download_history_repo()
        _download_history = repo.get_recent(limit=1000)
        logging.info(f"[WMD] Loaded {len(_download_history)} download history entries")
        return _download_history
    except Exception as e:
        logging.error(f"[WMD] Error loading download history: {e}")
        _download_history = []
        return _download_history


def save_download_history() -> bool:
    """Save is now automatic with DB - this is a no-op for compatibility"""
    return True


def add_to_download_history(download_info: Dict) -> None:
    """Add a download entry to history"""
    global _download_history

    entry = {
        'id': download_info.get('id', ''),
        'filename': download_info.get('filename', ''),
        'directory': download_info.get('directory', ''),
        'url': download_info.get('url', ''),
        'source': download_info.get('source', ''),
        'status': download_info.get('status', ''),
        'error': download_info.get('error', ''),
        'total_size': download_info.get('total_size', 0),
        'downloaded_at': datetime.now().isoformat()
    }

    try:
        repo = _get_download_history_repo()
        repo.add(entry)
        _download_history.insert(0, entry)
        logging.debug(f"[WMD] Added to download history: {entry['filename']}")
    except Exception as e:
        logging.error(f"[WMD] Error adding to download history: {e}")


def get_download_history() -> List[Dict]:
    """Get current download history"""
    global _download_history
    if not _download_history:
        load_download_history()
    return _download_history


def clear_download_history() -> bool:
    """Clear all download history"""
    global _download_history
    try:
        repo = _get_download_history_repo()
        repo.clear()
        _download_history = []
        return True
    except Exception as e:
        logging.error(f"[WMD] Error clearing download history: {e}")
        return False


# =============================================================================
# TAVILY/SEARCH CACHE FUNCTIONS (replaces tavily_cache.json operations)
# =============================================================================

_tavily_cache = {}


def load_tavily_cache() -> Dict:
    """Load Tavily search cache from database"""
    global _tavily_cache
    try:
        repo = _get_search_cache_repo()
        # Get all tavily entries
        db = get_db()
        rows = db.fetchall(
            "SELECT cache_key, result FROM search_cache WHERE source = 'tavily'"
        )
        _tavily_cache = {}
        for row in rows:
            try:
                _tavily_cache[row['cache_key']] = json.loads(row['result'])
            except:
                _tavily_cache[row['cache_key']] = row['result']
        logging.info(f"[WMD] Loaded Tavily cache with {len(_tavily_cache)} entries")
        return _tavily_cache
    except Exception as e:
        logging.error(f"[WMD] Error loading Tavily cache: {e}")
        _tavily_cache = {}
        return _tavily_cache


def save_tavily_cache() -> bool:
    """Save is now automatic with DB - this is a no-op for compatibility"""
    return True


def get_tavily_cached_result(filename: str) -> Optional[Dict]:
    """Get cached Tavily search result for a filename"""
    global _tavily_cache
    # Check in-memory cache first
    if filename in _tavily_cache:
        return _tavily_cache[filename]

    # Check database
    try:
        repo = _get_search_cache_repo()
        result = repo.get(filename, 'tavily')
        if result:
            _tavily_cache[filename] = result
            return result
    except Exception as e:
        logging.debug(f"[WMD] Error getting Tavily cache: {e}")

    return None


def set_tavily_cached_result(filename: str, data: Dict) -> None:
    """Cache Tavily search result for a filename"""
    global _tavily_cache
    data['cached_at'] = datetime.now().isoformat()
    _tavily_cache[filename] = data

    try:
        repo = _get_search_cache_repo()
        repo.set(filename, 'tavily', data, ttl=86400 * 7)  # 7 day TTL
    except Exception as e:
        logging.error(f"[WMD] Error caching Tavily result: {e}")


# =============================================================================
# MODEL METADATA FUNCTIONS (replaces model_metadata.json operations)
# =============================================================================

_model_metadata_cache = None


def get_model_metadata_all() -> Dict[str, Dict]:
    """Get all model metadata as a dictionary"""
    global _model_metadata_cache
    if _model_metadata_cache is not None:
        return _model_metadata_cache

    try:
        repo = _get_model_metadata_repo()
        db = get_db()
        rows = db.fetchall("SELECT * FROM model_metadata")
        _model_metadata_cache = {}
        for row in rows:
            row_dict = db.row_to_dict(row)
            filename = row_dict.get('filename', '')
            if filename:
                # Parse trigger_words if JSON
                if row_dict.get('trigger_words'):
                    try:
                        row_dict['trigger_words'] = json.loads(row_dict['trigger_words'])
                    except:
                        pass
                _model_metadata_cache[filename] = row_dict
        return _model_metadata_cache
    except Exception as e:
        logging.error(f"[WMD] Error loading model metadata: {e}")
        _model_metadata_cache = {}
        return _model_metadata_cache


def get_cached_metadata(filename: str) -> Optional[Dict]:
    """Get cached metadata for a filename"""
    all_metadata = get_model_metadata_all()
    basename = os.path.basename(filename)
    return all_metadata.get(filename) or all_metadata.get(basename)


def save_search_metadata(filename: str, metadata: Dict) -> bool:
    """Save search metadata for a filename"""
    global _model_metadata_cache
    basename = os.path.basename(filename)
    metadata['cached_at'] = datetime.now().isoformat()

    try:
        repo = _get_model_metadata_repo()

        # Get existing metadata to merge
        existing = get_cached_metadata(basename) or {}

        # Merge new metadata (don't overwrite user_url)
        for key, value in metadata.items():
            if key == 'user_url' and existing.get('user_url'):
                continue
            if value is not None and value != '':
                existing[key] = value

        existing['filename'] = basename
        repo.save(basename, existing)

        # Update cache
        if _model_metadata_cache is not None:
            _model_metadata_cache[basename] = existing

        return True
    except Exception as e:
        logging.error(f"[WMD] Error saving metadata: {e}")
        return False


def clear_model_metadata_cache():
    """Clear the model metadata cache to force reload"""
    global _model_metadata_cache
    _model_metadata_cache = None


def cache_download_url(filename: str, url: str, source: str,
                       hf_repo: str = None, hf_path: str = None,
                       model_name: str = None, civitai_url: str = None) -> None:
    """Cache URL after successful download for future use"""
    try:
        metadata = {
            'url': url,
            'source': f'download_{source}',
            'hf_repo': hf_repo or '',
            'hf_path': hf_path or '',
            'model_name': model_name or '',
            'civitai_url': civitai_url or '',
            'from_download': True
        }
        save_search_metadata(filename, metadata)
        logging.info(f"[WMD] Cached URL for: {filename}")
    except Exception as e:
        logging.error(f"[WMD] Failed to cache URL: {e}")


# =============================================================================
# USAGE CACHE FUNCTIONS (replaces usage_cache.json operations)
# =============================================================================

_usage_tracking = {}


def load_usage_cache() -> Dict:
    """Load usage tracking from database"""
    global _usage_tracking
    try:
        repo = _get_usage_cache_repo()
        db = get_db()
        rows = db.fetchall("SELECT * FROM usage_cache")
        _usage_tracking = {}
        for row in rows:
            row_dict = db.row_to_dict(row)
            filename = row_dict.get('filename', '')
            if filename:
                _usage_tracking[filename] = {
                    'last_used': row_dict.get('last_used'),
                    'use_count': row_dict.get('use_count', 0),
                    'directory': row_dict.get('directory', ''),
                    'workflows': []  # Not stored in DB yet
                }
        logging.info(f"[WMD] Loaded usage cache with {len(_usage_tracking)} models")
        return _usage_tracking
    except Exception as e:
        logging.error(f"[WMD] Error loading usage cache: {e}")
        _usage_tracking = {}
        return _usage_tracking


def save_usage_cache() -> bool:
    """Save is now automatic with DB - this is a no-op for compatibility"""
    return True


def get_usage_tracking() -> Dict:
    """Get current usage tracking data"""
    global _usage_tracking
    if not _usage_tracking:
        load_usage_cache()
    return _usage_tracking


def track_model_usage(filename: str, directory: str = '', workflow_name: str = None) -> None:
    """Track usage of a model"""
    global _usage_tracking

    try:
        repo = _get_usage_cache_repo()
        repo.track_usage(filename, directory)

        # Update in-memory cache
        if filename not in _usage_tracking:
            _usage_tracking[filename] = {'last_used': None, 'use_count': 0, 'workflows': []}

        _usage_tracking[filename]['last_used'] = datetime.now().timestamp()
        _usage_tracking[filename]['use_count'] = _usage_tracking[filename].get('use_count', 0) + 1

        if workflow_name:
            workflows = _usage_tracking[filename].get('workflows', [])
            if workflow_name not in workflows:
                workflows.append(workflow_name)
                _usage_tracking[filename]['workflows'] = workflows[-10:]

    except Exception as e:
        logging.error(f"[WMD] Error tracking usage: {e}")


# =============================================================================
# NODE METADATA FUNCTIONS (replaces node_metadata.json operations)
# =============================================================================

_node_metadata_cache = None


def load_node_metadata() -> Dict:
    """Load node metadata from database"""
    global _node_metadata_cache
    try:
        repo = _get_node_metadata_repo()
        _node_metadata_cache = repo.get_all()
        return _node_metadata_cache
    except Exception as e:
        logging.error(f"[WMD] Error loading node metadata: {e}")
        _node_metadata_cache = {}
        return _node_metadata_cache


def save_node_metadata(node_type: str, metadata: Dict) -> bool:
    """Save node metadata"""
    global _node_metadata_cache
    try:
        repo = _get_node_metadata_repo()
        repo.save(node_type, metadata)
        if _node_metadata_cache is not None:
            _node_metadata_cache[node_type] = metadata
        return True
    except Exception as e:
        logging.error(f"[WMD] Error saving node metadata: {e}")
        return False


def get_node_metadata(node_type: str) -> Optional[Dict]:
    """Get metadata for a specific node type"""
    if _node_metadata_cache is None:
        load_node_metadata()
    return _node_metadata_cache.get(node_type)


# =============================================================================
# MODEL ALIAS FUNCTIONS (replaces model-aliases.json operations)
# =============================================================================

_model_aliases_cache = None


def load_model_aliases() -> Dict[str, str]:
    """Load model aliases from database"""
    global _model_aliases_cache
    try:
        repo = _get_model_alias_repo()
        db = get_db()
        rows = db.fetchall("SELECT alias, canonical_name FROM model_aliases")
        _model_aliases_cache = {row['alias']: row['canonical_name'] for row in rows}
        return _model_aliases_cache
    except Exception as e:
        logging.error(f"[WMD] Error loading model aliases: {e}")
        _model_aliases_cache = {}
        return _model_aliases_cache


def get_canonical_name(alias: str) -> Optional[str]:
    """Get canonical name for an alias"""
    if _model_aliases_cache is None:
        load_model_aliases()
    return _model_aliases_cache.get(alias)


def add_model_alias(alias: str, canonical_name: str, source: str = '') -> bool:
    """Add a model alias"""
    global _model_aliases_cache
    try:
        repo = _get_model_alias_repo()
        repo.add(alias, canonical_name, source)
        if _model_aliases_cache is not None:
            _model_aliases_cache[alias] = canonical_name
        return True
    except Exception as e:
        logging.error(f"[WMD] Error adding alias: {e}")
        return False


# =============================================================================
# MODEL CATALOG FUNCTIONS (replaces model_catalog.json operations)
# =============================================================================

def lookup_catalog(filename: str) -> Optional[Dict]:
    """Look up a model in the catalog"""
    try:
        repo = _get_model_catalog_repo()
        return repo.lookup(filename)
    except Exception as e:
        logging.error(f"[WMD] Error looking up catalog: {e}")
        return None


def add_to_catalog(entry: Dict) -> bool:
    """Add a model to the catalog"""
    try:
        repo = _get_model_catalog_repo()
        repo.add(entry)
        return True
    except Exception as e:
        logging.error(f"[WMD] Error adding to catalog: {e}")
        return False


def get_catalog_by_type(model_type: str) -> List[Dict]:
    """Get catalog entries by model type"""
    try:
        repo = _get_model_catalog_repo()
        return repo.get_by_type(model_type)
    except Exception as e:
        logging.error(f"[WMD] Error getting catalog by type: {e}")
        return []


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_storage():
    """Initialize storage and run auto-migration if needed"""
    try:
        from .migrate_to_sqlite import auto_migrate
        auto_migrate()
        logging.info("[WMD] Storage initialized")
    except Exception as e:
        logging.error(f"[WMD] Error initializing storage: {e}")


# Auto-initialize on import
try:
    init_storage()
except:
    pass
