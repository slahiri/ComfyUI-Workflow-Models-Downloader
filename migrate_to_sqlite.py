"""
Migration Script: JSON to SQLite

One-time migration from legacy JSON files to SQLite database.
Run this script to migrate existing data, or it will run automatically on first use.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extension path
EXTENSION_PATH = os.path.dirname(__file__)

# JSON file paths
JSON_FILES = {
    'settings': os.path.join(EXTENSION_PATH, 'settings.json'),
    'download_history': os.path.join(EXTENSION_PATH, 'download_history.json'),
    'model_metadata': os.path.join(EXTENSION_PATH, 'model_metadata.json'),
    'model_catalog': os.path.join(EXTENSION_PATH, 'model_catalog.json'),
    'tavily_cache': os.path.join(EXTENSION_PATH, 'tavily_cache.json'),
    'search_cache': os.path.join(EXTENSION_PATH, 'search_cache.json'),
    'usage_cache': os.path.join(EXTENSION_PATH, 'usage_cache.json'),
    'node_metadata': os.path.join(EXTENSION_PATH, 'node_metadata.json'),
    'model_aliases': os.path.join(EXTENSION_PATH, 'metadata', 'model-aliases.json'),
}


def load_json_file(filepath: str) -> Optional[Any]:
    """Load JSON file if it exists."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"[WMD] Failed to load {filepath}: {e}")
        return None


def backup_json_file(filepath: str) -> bool:
    """Create .bak backup of JSON file."""
    if not os.path.exists(filepath):
        return False
    backup_path = filepath + '.bak'
    try:
        os.rename(filepath, backup_path)
        logger.info(f"[WMD] Backed up {filepath} -> {backup_path}")
        return True
    except OSError as e:
        logger.warning(f"[WMD] Failed to backup {filepath}: {e}")
        return False


def migrate_settings(db) -> int:
    """Migrate settings.json to database."""
    data = load_json_file(JSON_FILES['settings'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        for key, value in data.items():
            db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value) if not isinstance(value, str) else value)
            )
            count += 1

    logger.info(f"[WMD] Migrated {count} settings")
    return count


def migrate_download_history(db) -> int:
    """Migrate download_history.json to database."""
    data = load_json_file(JSON_FILES['download_history'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        # Handle both list and dict formats
        entries = data if isinstance(data, list) else list(data.values())

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            db.execute("""
                INSERT OR REPLACE INTO download_history
                (id, filename, directory, url, source, status, error, total_size, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get('id', entry.get('filename', '')),
                entry.get('filename', ''),
                entry.get('directory', ''),
                entry.get('url', ''),
                entry.get('source', ''),
                entry.get('status', 'completed'),
                entry.get('error'),
                entry.get('total_size', 0),
                entry.get('downloaded_at', entry.get('timestamp', datetime.now().isoformat()))
            ))
            count += 1

    logger.info(f"[WMD] Migrated {count} download history entries")
    return count


def migrate_model_metadata(db) -> int:
    """Migrate model_metadata.json to database."""
    data = load_json_file(JSON_FILES['model_metadata'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        for filename, meta in data.items():
            if not isinstance(meta, dict):
                continue

            db.execute("""
                INSERT OR REPLACE INTO model_metadata
                (filename, url, source, hf_repo, hf_path, civitai_url, civitai_model_id,
                 civitai_version_id, model_name, model_type, base_model, sha256_hash,
                 file_size, user_url, trigger_words)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                meta.get('url', ''),
                meta.get('source', ''),
                meta.get('hf_repo', ''),
                meta.get('hf_path', ''),
                meta.get('civitai_url', ''),
                meta.get('civitai_model_id', ''),
                meta.get('civitai_version_id', ''),
                meta.get('model_name', ''),
                meta.get('model_type', ''),
                meta.get('base_model', ''),
                meta.get('sha256_hash', ''),
                meta.get('file_size', 0),
                meta.get('user_url', ''),
                json.dumps(meta.get('trigger_words', [])) if meta.get('trigger_words') else None
            ))
            count += 1

    logger.info(f"[WMD] Migrated {count} model metadata entries")
    return count


def migrate_model_catalog(db) -> int:
    """Migrate model_catalog.json to database."""
    data = load_json_file(JSON_FILES['model_catalog'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        # Handle both list and dict formats
        if isinstance(data, dict):
            entries = list(data.values())
        else:
            entries = data

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            db.execute("""
                INSERT OR REPLACE INTO model_catalog
                (filename, source, repo_id, hf_path, civitai_model_id, civitai_version_id,
                 model_type, local_path, base_model, protected, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get('filename', ''),
                entry.get('source', ''),
                entry.get('repo_id', entry.get('hf_repo', '')),
                entry.get('hf_path', ''),
                entry.get('civitai_model_id', ''),
                entry.get('civitai_version_id', ''),
                entry.get('model_type', entry.get('type', '')),
                entry.get('local_path', ''),
                entry.get('base_model', ''),
                1 if entry.get('protected') else 0,
                json.dumps(entry.get('tags', [])) if entry.get('tags') else None
            ))
            count += 1

    logger.info(f"[WMD] Migrated {count} model catalog entries")
    return count


def migrate_search_cache(db) -> int:
    """Migrate search caches (tavily_cache, search_cache) to database."""
    count = 0

    # Migrate tavily cache
    tavily_data = load_json_file(JSON_FILES['tavily_cache'])
    if tavily_data and isinstance(tavily_data, dict):
        with db.transaction():
            for query, result in tavily_data.items():
                db.execute("""
                    INSERT OR REPLACE INTO search_cache
                    (cache_key, source, result, cached_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    query,
                    'tavily',
                    json.dumps(result) if not isinstance(result, str) else result,
                    datetime.now().isoformat()
                ))
                count += 1
        logger.info(f"[WMD] Migrated {count} tavily cache entries")

    # Migrate general search cache
    search_data = load_json_file(JSON_FILES['search_cache'])
    if search_data and isinstance(search_data, dict):
        search_count = 0
        with db.transaction():
            for key, result in search_data.items():
                # Try to determine source from key
                source = 'unknown'
                if 'civitai' in key.lower():
                    source = 'civitai'
                elif 'huggingface' in key.lower() or 'hf' in key.lower():
                    source = 'huggingface'

                db.execute("""
                    INSERT OR REPLACE INTO search_cache
                    (cache_key, source, result, cached_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    key,
                    source,
                    json.dumps(result) if not isinstance(result, str) else result,
                    datetime.now().isoformat()
                ))
                search_count += 1
        count += search_count
        logger.info(f"[WMD] Migrated {search_count} search cache entries")

    return count


def migrate_usage_cache(db) -> int:
    """Migrate usage_cache.json to database."""
    data = load_json_file(JSON_FILES['usage_cache'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        for filename, usage in data.items():
            if isinstance(usage, dict):
                db.execute("""
                    INSERT OR REPLACE INTO usage_cache
                    (filename, directory, use_count, last_used, first_used)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    filename,
                    usage.get('directory', ''),
                    usage.get('use_count', usage.get('count', 1)),
                    usage.get('last_used'),
                    usage.get('first_used', datetime.now().isoformat())
                ))
            else:
                # Simple count format
                db.execute("""
                    INSERT OR REPLACE INTO usage_cache
                    (filename, use_count)
                    VALUES (?, ?)
                """, (filename, usage if isinstance(usage, int) else 1))
            count += 1

    logger.info(f"[WMD] Migrated {count} usage cache entries")
    return count


def migrate_node_metadata(db) -> int:
    """Migrate node_metadata.json to database."""
    data = load_json_file(JSON_FILES['node_metadata'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        for node_type, meta in data.items():
            if not isinstance(meta, dict):
                continue

            db.execute("""
                INSERT OR REPLACE INTO node_metadata
                (node_type, input_fields, output_fields, category)
                VALUES (?, ?, ?, ?)
            """, (
                node_type,
                json.dumps(meta.get('input_fields', meta.get('inputs', []))),
                json.dumps(meta.get('output_fields', meta.get('outputs', []))),
                meta.get('category', '')
            ))
            count += 1

    logger.info(f"[WMD] Migrated {count} node metadata entries")
    return count


def migrate_model_aliases(db) -> int:
    """Migrate model-aliases.json to database."""
    data = load_json_file(JSON_FILES['model_aliases'])
    if not data:
        return 0

    count = 0
    with db.transaction():
        for alias, canonical in data.items():
            if isinstance(canonical, dict):
                canonical_name = canonical.get('canonical', canonical.get('name', ''))
                source = canonical.get('source', '')
            else:
                canonical_name = canonical
                source = ''

            db.execute("""
                INSERT OR REPLACE INTO model_aliases
                (alias, canonical_name, source)
                VALUES (?, ?, ?)
            """, (alias, canonical_name, source))
            count += 1

    logger.info(f"[WMD] Migrated {count} model aliases")
    return count


def run_migration(backup: bool = True) -> Dict[str, int]:
    """
    Run the full migration from JSON to SQLite.

    Args:
        backup: If True, rename JSON files to .bak after migration

    Returns:
        Dictionary with migration counts for each table
    """
    from .database import get_db

    db = get_db()
    results = {}

    logger.info("[WMD] Starting JSON to SQLite migration...")

    # Run all migrations
    results['settings'] = migrate_settings(db)
    results['download_history'] = migrate_download_history(db)
    results['model_metadata'] = migrate_model_metadata(db)
    results['model_catalog'] = migrate_model_catalog(db)
    results['search_cache'] = migrate_search_cache(db)
    results['usage_cache'] = migrate_usage_cache(db)
    results['node_metadata'] = migrate_node_metadata(db)
    results['model_aliases'] = migrate_model_aliases(db)

    total = sum(results.values())
    logger.info(f"[WMD] Migration complete. Total records migrated: {total}")

    # Backup JSON files
    if backup:
        logger.info("[WMD] Backing up JSON files...")
        for name, filepath in JSON_FILES.items():
            backup_json_file(filepath)

    return results


def check_migration_needed() -> bool:
    """Check if migration is needed (JSON files exist but DB is empty)."""
    from .database import get_db

    # Check if any JSON files exist
    json_exists = any(os.path.exists(f) for f in JSON_FILES.values())
    if not json_exists:
        return False

    # Check if DB has data
    db = get_db()
    row = db.fetchone("SELECT COUNT(*) as cnt FROM settings")
    if row and row['cnt'] > 0:
        return False  # Already migrated

    return True


def auto_migrate():
    """Auto-migrate if needed. Call this on extension startup."""
    if check_migration_needed():
        logger.info("[WMD] JSON files detected, starting auto-migration...")
        run_migration(backup=True)
    else:
        logger.debug("[WMD] No migration needed")


if __name__ == '__main__':
    # Run migration directly
    import sys
    sys.path.insert(0, os.path.dirname(EXTENSION_PATH))

    from database import get_db
    run_migration(backup=True)
