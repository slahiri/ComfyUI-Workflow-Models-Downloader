"""
Repository Classes for Workflow Models Downloader

Provides data access layer for all entities.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict

from .database import get_db


class SettingsRepository:
    """Repository for user settings."""

    def __init__(self):
        self.db = get_db()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        row = self.db.fetchone(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        if row:
            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                return row['value']
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        json_value = json.dumps(value) if not isinstance(value, str) else value
        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json_value))

    def get_all(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        rows = self.db.fetchall("SELECT key, value FROM settings")
        result = {}
        for row in rows:
            try:
                result[row['key']] = json.loads(row['value'])
            except json.JSONDecodeError:
                result[row['key']] = row['value']
        return result

    def set_all(self, settings: Dict[str, Any]) -> None:
        """Set multiple settings at once."""
        with self.db.transaction():
            for key, value in settings.items():
                json_value = json.dumps(value) if not isinstance(value, str) else value
                self.db.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, json_value))

    def delete(self, key: str) -> None:
        """Delete a setting."""
        with self.db.transaction():
            self.db.execute("DELETE FROM settings WHERE key = ?", (key,))


class DownloadHistoryRepository:
    """Repository for download history."""

    def __init__(self):
        self.db = get_db()

    def add(self, entry: Dict[str, Any]) -> None:
        """Add or update a download history entry."""
        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO download_history
                (id, filename, directory, url, source, status, error, total_size, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                entry.get('id', ''),
                entry.get('filename', ''),
                entry.get('directory', ''),
                entry.get('url', ''),
                entry.get('source', ''),
                entry.get('status', ''),
                entry.get('error', ''),
                entry.get('total_size', 0)
            ))

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a download entry by ID."""
        row = self.db.fetchone(
            "SELECT * FROM download_history WHERE id = ?",
            (id,)
        )
        return self.db.row_to_dict(row)

    def get_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get a download entry by filename."""
        row = self.db.fetchone(
            "SELECT * FROM download_history WHERE filename = ? ORDER BY downloaded_at DESC LIMIT 1",
            (filename,)
        )
        return self.db.row_to_dict(row)

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent download history entries."""
        rows = self.db.fetchall(
            "SELECT * FROM download_history ORDER BY downloaded_at DESC LIMIT ?",
            (limit,)
        )
        return self.db.rows_to_dicts(rows)

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get entries by status."""
        rows = self.db.fetchall(
            "SELECT * FROM download_history WHERE status = ? ORDER BY downloaded_at DESC",
            (status,)
        )
        return self.db.rows_to_dicts(rows)

    def update_status(self, id: str, status: str, error: str = None) -> None:
        """Update download status."""
        with self.db.transaction():
            if error:
                self.db.execute(
                    "UPDATE download_history SET status = ?, error = ? WHERE id = ?",
                    (status, error, id)
                )
            else:
                self.db.execute(
                    "UPDATE download_history SET status = ? WHERE id = ?",
                    (status, id)
                )

    def delete(self, id: str) -> None:
        """Delete a download entry."""
        with self.db.transaction():
            self.db.execute("DELETE FROM download_history WHERE id = ?", (id,))

    def clear(self) -> None:
        """Clear all download history."""
        with self.db.transaction():
            self.db.execute("DELETE FROM download_history")


class ModelMetadataRepository:
    """Repository for model metadata."""

    def __init__(self):
        self.db = get_db()

    def get(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model by filename."""
        row = self.db.fetchone(
            "SELECT * FROM model_metadata WHERE filename = ?",
            (filename,)
        )
        if row:
            result = self.db.row_to_dict(row)
            # Parse trigger_words JSON
            if result.get('trigger_words'):
                try:
                    result['trigger_words'] = json.loads(result['trigger_words'])
                except json.JSONDecodeError:
                    pass
            return result
        return None

    def save(self, filename: str, metadata: Dict[str, Any]) -> None:
        """Save or update model metadata."""
        # Serialize trigger_words to JSON
        trigger_words = metadata.get('trigger_words')
        if isinstance(trigger_words, list):
            trigger_words = json.dumps(trigger_words)

        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO model_metadata
                (filename, url, source, hf_repo, hf_path, civitai_url,
                 civitai_model_id, civitai_version_id, model_name, model_type,
                 base_model, sha256_hash, file_size, user_url, trigger_words,
                 cached_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                filename,
                metadata.get('url', ''),
                metadata.get('source', ''),
                metadata.get('hf_repo', ''),
                metadata.get('hf_path', ''),
                metadata.get('civitai_url', ''),
                metadata.get('civitai_model_id', ''),
                metadata.get('civitai_version_id', ''),
                metadata.get('model_name', ''),
                metadata.get('model_type', ''),
                metadata.get('base_model', ''),
                metadata.get('sha256_hash', ''),
                metadata.get('file_size', 0),
                metadata.get('user_url', ''),
                trigger_words,
                metadata.get('cached_at', datetime.now().isoformat())
            ))

    def get_by_hash(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        """Get metadata by SHA256 hash."""
        row = self.db.fetchone(
            "SELECT * FROM model_metadata WHERE sha256_hash = ?",
            (sha256_hash,)
        )
        return self.db.row_to_dict(row)

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get all metadata for a source."""
        rows = self.db.fetchall(
            "SELECT * FROM model_metadata WHERE source = ?",
            (source,)
        )
        return self.db.rows_to_dicts(rows)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all metadata as a dictionary keyed by filename."""
        rows = self.db.fetchall("SELECT * FROM model_metadata")
        return {row['filename']: self.db.row_to_dict(row) for row in rows}

    def delete(self, filename: str) -> None:
        """Delete metadata for a model."""
        with self.db.transaction():
            self.db.execute("DELETE FROM model_metadata WHERE filename = ?", (filename,))

    def search(self, **filters) -> List[Dict[str, Any]]:
        """Search metadata with filters."""
        conditions = []
        params = []

        for key, value in filters.items():
            if value is not None:
                conditions.append(f"{key} = ?")
                params.append(value)

        sql = "SELECT * FROM model_metadata"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        rows = self.db.fetchall(sql, tuple(params))
        return self.db.rows_to_dicts(rows)


class ModelCatalogRepository:
    """Repository for curated model catalog."""

    def __init__(self):
        self.db = get_db()

    def lookup(self, filename: str) -> Optional[Dict[str, Any]]:
        """Look up a model in the catalog."""
        # Exact match first
        row = self.db.fetchone(
            "SELECT * FROM model_catalog WHERE filename = ?",
            (filename,)
        )
        if row:
            result = self.db.row_to_dict(row)
            result['protected'] = bool(result.get('protected'))
            if result.get('tags'):
                try:
                    result['tags'] = json.loads(result['tags'])
                except json.JSONDecodeError:
                    result['tags'] = []
            return result

        # Try case-insensitive match
        row = self.db.fetchone(
            "SELECT * FROM model_catalog WHERE LOWER(filename) = LOWER(?)",
            (filename,)
        )
        if row:
            result = self.db.row_to_dict(row)
            result['protected'] = bool(result.get('protected'))
            if result.get('tags'):
                try:
                    result['tags'] = json.loads(result['tags'])
                except json.JSONDecodeError:
                    result['tags'] = []
            return result

        return None

    def add(self, entry: Dict[str, Any]) -> None:
        """Add or update a catalog entry."""
        tags = entry.get('tags', [])
        if isinstance(tags, list):
            tags = json.dumps(tags)

        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO model_catalog
                (filename, source, repo_id, hf_path, civitai_model_id,
                 civitai_version_id, model_type, local_path, base_model,
                 protected, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.get('filename', ''),
                entry.get('source', ''),
                entry.get('repo_id', ''),
                entry.get('hf_path', ''),
                entry.get('civitai_model_id', ''),
                entry.get('civitai_version_id', ''),
                entry.get('model_type', ''),
                entry.get('local_path', ''),
                entry.get('base_model', ''),
                1 if entry.get('protected') else 0,
                tags
            ))

    def get_by_type(self, model_type: str) -> List[Dict[str, Any]]:
        """Get catalog entries by model type."""
        rows = self.db.fetchall(
            "SELECT * FROM model_catalog WHERE model_type = ?",
            (model_type,)
        )
        return self.db.rows_to_dicts(rows)

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get catalog entries by source."""
        rows = self.db.fetchall(
            "SELECT * FROM model_catalog WHERE source = ?",
            (source,)
        )
        return self.db.rows_to_dicts(rows)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all catalog entries."""
        rows = self.db.fetchall("SELECT * FROM model_catalog ORDER BY filename")
        results = []
        for row in rows:
            entry = self.db.row_to_dict(row)
            entry['protected'] = bool(entry.get('protected'))
            if entry.get('tags'):
                try:
                    entry['tags'] = json.loads(entry['tags'])
                except json.JSONDecodeError:
                    entry['tags'] = []
            results.append(entry)
        return results

    def delete(self, filename: str) -> None:
        """Delete a catalog entry."""
        with self.db.transaction():
            self.db.execute("DELETE FROM model_catalog WHERE filename = ?", (filename,))

    def count(self) -> int:
        """Get total catalog entries."""
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM model_catalog")
        return row['cnt'] if row else 0


class SearchCacheRepository:
    """Repository for search cache (Tavily, API results)."""

    def __init__(self):
        self.db = get_db()

    def get(self, cache_key: str, source: str = None) -> Optional[Dict[str, Any]]:
        """Get cached search result."""
        if source:
            row = self.db.fetchone(
                """SELECT * FROM search_cache
                   WHERE cache_key = ? AND source = ?
                   AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)""",
                (cache_key, source)
            )
        else:
            row = self.db.fetchone(
                """SELECT * FROM search_cache
                   WHERE cache_key = ?
                   AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)""",
                (cache_key,)
            )

        if row:
            result = self.db.row_to_dict(row)
            try:
                result['result'] = json.loads(result['result'])
            except json.JSONDecodeError:
                pass
            return result
        return None

    def set(self, cache_key: str, source: str, result: Any, ttl_seconds: int = 3600) -> None:
        """Cache a search result."""
        result_json = json.dumps(result) if not isinstance(result, str) else result
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds > 0 else None

        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO search_cache
                (cache_key, source, result, cached_at, expires_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (cache_key, source, result_json, expires_at))

    def delete(self, cache_key: str) -> None:
        """Delete a cache entry."""
        with self.db.transaction():
            self.db.execute("DELETE FROM search_cache WHERE cache_key = ?", (cache_key,))

    def cleanup_expired(self) -> int:
        """Remove expired cache entries. Returns count of deleted entries."""
        with self.db.transaction():
            cursor = self.db.execute(
                "DELETE FROM search_cache WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP"
            )
            return cursor.rowcount

    def clear_by_source(self, source: str) -> None:
        """Clear all cache entries for a source."""
        with self.db.transaction():
            self.db.execute("DELETE FROM search_cache WHERE source = ?", (source,))

    def clear_all(self) -> None:
        """Clear all cache entries."""
        with self.db.transaction():
            self.db.execute("DELETE FROM search_cache")


class UsageCacheRepository:
    """Repository for model usage tracking."""

    def __init__(self):
        self.db = get_db()

    def track_usage(self, filename: str, directory: str = None) -> None:
        """Track model usage."""
        with self.db.transaction():
            # Try to update existing
            cursor = self.db.execute("""
                UPDATE usage_cache
                SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP
                WHERE filename = ?
            """, (filename,))

            # Insert if not exists
            if cursor.rowcount == 0:
                self.db.execute("""
                    INSERT INTO usage_cache (filename, directory, use_count, last_used, first_used)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (filename, directory))

    def get(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get usage info for a model."""
        row = self.db.fetchone(
            "SELECT * FROM usage_cache WHERE filename = ?",
            (filename,)
        )
        return self.db.row_to_dict(row)

    def get_most_used(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most used models."""
        rows = self.db.fetchall(
            "SELECT * FROM usage_cache ORDER BY use_count DESC LIMIT ?",
            (limit,)
        )
        return self.db.rows_to_dicts(rows)

    def get_recently_used(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently used models."""
        rows = self.db.fetchall(
            "SELECT * FROM usage_cache ORDER BY last_used DESC LIMIT ?",
            (limit,)
        )
        return self.db.rows_to_dicts(rows)

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all usage data as a dictionary."""
        rows = self.db.fetchall("SELECT * FROM usage_cache")
        return {row['filename']: self.db.row_to_dict(row) for row in rows}

    def delete(self, filename: str) -> None:
        """Delete usage data for a model."""
        with self.db.transaction():
            self.db.execute("DELETE FROM usage_cache WHERE filename = ?", (filename,))


class NodeMetadataRepository:
    """Repository for node metadata cache."""

    def __init__(self):
        self.db = get_db()

    def get(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a node type."""
        row = self.db.fetchone(
            "SELECT * FROM node_metadata WHERE node_type = ?",
            (node_type,)
        )
        if row:
            result = self.db.row_to_dict(row)
            for field in ['input_fields', 'output_fields']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        pass
            return result
        return None

    def save(self, node_type: str, metadata: Dict[str, Any]) -> None:
        """Save node metadata."""
        input_fields = metadata.get('input_fields')
        output_fields = metadata.get('output_fields')

        if isinstance(input_fields, (list, dict)):
            input_fields = json.dumps(input_fields)
        if isinstance(output_fields, (list, dict)):
            output_fields = json.dumps(output_fields)

        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO node_metadata
                (node_type, input_fields, output_fields, category, cached_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                node_type,
                input_fields,
                output_fields,
                metadata.get('category', '')
            ))

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all node metadata."""
        rows = self.db.fetchall("SELECT * FROM node_metadata")
        result = {}
        for row in rows:
            entry = self.db.row_to_dict(row)
            for field in ['input_fields', 'output_fields']:
                if entry.get(field):
                    try:
                        entry[field] = json.loads(entry[field])
                    except json.JSONDecodeError:
                        pass
            result[row['node_type']] = entry
        return result

    def delete(self, node_type: str) -> None:
        """Delete node metadata."""
        with self.db.transaction():
            self.db.execute("DELETE FROM node_metadata WHERE node_type = ?", (node_type,))

    def clear_all(self) -> None:
        """Clear all node metadata."""
        with self.db.transaction():
            self.db.execute("DELETE FROM node_metadata")


class ModelAliasRepository:
    """Repository for model name aliases."""

    def __init__(self):
        self.db = get_db()

    def get_canonical(self, alias: str) -> Optional[str]:
        """Get canonical name for an alias."""
        row = self.db.fetchone(
            "SELECT canonical_name FROM model_aliases WHERE alias = ?",
            (alias,)
        )
        return row['canonical_name'] if row else None

    def add(self, alias: str, canonical_name: str, source: str = None) -> None:
        """Add an alias mapping."""
        with self.db.transaction():
            self.db.execute("""
                INSERT OR REPLACE INTO model_aliases (alias, canonical_name, source)
                VALUES (?, ?, ?)
            """, (alias, canonical_name, source))

    def get_aliases(self, canonical_name: str) -> List[str]:
        """Get all aliases for a canonical name."""
        rows = self.db.fetchall(
            "SELECT alias FROM model_aliases WHERE canonical_name = ?",
            (canonical_name,)
        )
        return [row['alias'] for row in rows]

    def get_all(self) -> Dict[str, str]:
        """Get all alias mappings."""
        rows = self.db.fetchall("SELECT alias, canonical_name FROM model_aliases")
        return {row['alias']: row['canonical_name'] for row in rows}

    def delete(self, alias: str) -> None:
        """Delete an alias."""
        with self.db.transaction():
            self.db.execute("DELETE FROM model_aliases WHERE alias = ?", (alias,))
