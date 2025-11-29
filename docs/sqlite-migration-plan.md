# SQLite Migration Plan

## Overview

Migrate from multiple JSON files to a single SQLite database for better performance, concurrent access, and query capabilities.

---

## Current JSON Files

| File | Purpose | Size Concern |
|------|---------|--------------|
| `settings.json` | User settings (tokens, preferences) | Small |
| `download_history.json` | Download history entries | Can grow large |
| `tavily_cache.json` | Tavily search cache | Medium |
| `usage_cache.json` | Model usage tracking | Medium |
| `node_metadata.json` | Node metadata cache | Medium |
| `model_metadata.json` | Model metadata/sources | Can grow large |
| `model_catalog.json` | Curated model catalog | Small-Medium |
| `metadata/model-aliases.json` | Model name aliases | Small |

---

## Benefits of SQLite

| Benefit | Description |
|---------|-------------|
| **Performance** | Faster queries with indexing, no full file parsing |
| **Concurrent Access** | Built-in locking for multi-thread safety |
| **ACID Transactions** | Reliable writes, no corrupt JSON |
| **Query Power** | SQL queries for complex lookups |
| **Single File** | One `.db` file instead of many `.json` files |
| **Space Efficiency** | Better compression, no duplicate keys |
| **Migration** | Can run old + new in parallel during transition |

---

## Database Schema

### File: `wmd_data.db`

```sql
-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Download history
CREATE TABLE IF NOT EXISTS download_history (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    directory TEXT,
    url TEXT,
    source TEXT,
    status TEXT NOT NULL,
    error TEXT,
    total_size INTEGER DEFAULT 0,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(filename, directory)
);
CREATE INDEX idx_download_history_filename ON download_history(filename);
CREATE INDEX idx_download_history_status ON download_history(status);

-- Model metadata (sources, URLs, etc.)
CREATE TABLE IF NOT EXISTS model_metadata (
    filename TEXT PRIMARY KEY,
    url TEXT,
    source TEXT,
    hf_repo TEXT,
    hf_path TEXT,
    civitai_url TEXT,
    civitai_model_id TEXT,
    civitai_version_id TEXT,
    model_name TEXT,
    model_type TEXT,
    base_model TEXT,
    sha256_hash TEXT,
    file_size INTEGER,
    user_url TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_model_metadata_source ON model_metadata(source);
CREATE INDEX idx_model_metadata_hash ON model_metadata(sha256_hash);

-- Model catalog (curated entries)
CREATE TABLE IF NOT EXISTS model_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    repo_id TEXT,
    hf_path TEXT,
    civitai_model_id TEXT,
    civitai_version_id TEXT,
    model_type TEXT,
    local_path TEXT,
    base_model TEXT,
    protected BOOLEAN DEFAULT FALSE,
    tags TEXT,  -- JSON array as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_catalog_source ON model_catalog(source);
CREATE INDEX idx_catalog_model_type ON model_catalog(model_type);

-- Search cache (Tavily, API results)
CREATE TABLE IF NOT EXISTS search_cache (
    query TEXT PRIMARY KEY,
    source TEXT NOT NULL,  -- 'tavily', 'huggingface', 'civitai'
    result TEXT NOT NULL,  -- JSON blob
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
CREATE INDEX idx_search_cache_source ON search_cache(source);
CREATE INDEX idx_search_cache_expires ON search_cache(expires_at);

-- Usage tracking
CREATE TABLE IF NOT EXISTS usage_cache (
    filename TEXT PRIMARY KEY,
    directory TEXT,
    use_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_usage_last_used ON usage_cache(last_used);

-- Node metadata
CREATE TABLE IF NOT EXISTS node_metadata (
    node_type TEXT PRIMARY KEY,
    input_fields TEXT,  -- JSON blob
    output_fields TEXT, -- JSON blob
    category TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model aliases
CREATE TABLE IF NOT EXISTS model_aliases (
    alias TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    source TEXT
);
CREATE INDEX idx_aliases_canonical ON model_aliases(canonical_name);

-- Database version for migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Plan

### Phase 1: Database Layer (Foundation)

**File: `database.py`**

```python
import sqlite3
import threading
import json
import os
import logging
from contextlib import contextmanager
from typing import Any, Optional, Dict, List

class Database:
    """Thread-safe SQLite database wrapper"""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: str = None) -> 'Database':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if db_path is None:
                        db_path = os.path.join(os.path.dirname(__file__), 'wmd_data.db')
                    cls._instance = cls(db_path)
        return cls._instance

    @property
    def conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def transaction(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params: List[tuple]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        return self.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        return self.execute(sql, params).fetchall()

    def _init_db(self):
        # Create tables from schema
        pass
```

### Phase 2: Repository Classes

**Repositories for each data type:**

```python
class SettingsRepository:
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def get_all(self) -> Dict[str, Any]
    def delete(self, key: str) -> None

class DownloadHistoryRepository:
    def add(self, entry: Dict) -> None
    def get_by_filename(self, filename: str) -> Optional[Dict]
    def get_recent(self, limit: int = 100) -> List[Dict]
    def clear(self) -> None
    def delete(self, id: str) -> None

class ModelMetadataRepository:
    def get(self, filename: str) -> Optional[Dict]
    def save(self, filename: str, metadata: Dict) -> None
    def get_by_hash(self, sha256: str) -> Optional[Dict]
    def search(self, **filters) -> List[Dict]

class ModelCatalogRepository:
    def lookup(self, filename: str) -> Optional[Dict]
    def add(self, entry: Dict) -> None
    def get_by_type(self, model_type: str) -> List[Dict]
    def get_all(self) -> List[Dict]

class SearchCacheRepository:
    def get(self, query: str, source: str) -> Optional[Dict]
    def set(self, query: str, source: str, result: Dict, ttl: int = 3600) -> None
    def cleanup_expired(self) -> int
```

### Phase 3: Migration Script

**File: `migrate_to_sqlite.py`**

```python
def migrate_json_to_sqlite():
    """One-time migration from JSON to SQLite"""

    db = Database.get_instance()

    # 1. Migrate settings
    if os.path.exists('settings.json'):
        with open('settings.json') as f:
            settings = json.load(f)
        for key, value in settings.items():
            db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )

    # 2. Migrate download history
    if os.path.exists('download_history.json'):
        with open('download_history.json') as f:
            history = json.load(f)
        for entry in history:
            db.execute("""
                INSERT OR REPLACE INTO download_history
                (id, filename, directory, status, error, total_size, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (...))

    # 3. Migrate model metadata
    # 4. Migrate catalog
    # 5. Migrate caches

    db.conn.commit()

    # Rename old files to .bak
    for f in ['settings.json', 'download_history.json', ...]:
        if os.path.exists(f):
            os.rename(f, f + '.bak')
```

### Phase 4: Update server.py

Replace JSON file operations with repository calls:

```python
# Before
def load_settings():
    with open(SETTINGS_FILE) as f:
        return json.load(f)

# After
def load_settings():
    return SettingsRepository().get_all()
```

### Phase 5: Backward Compatibility

```python
def get_storage_backend():
    """Check if using SQLite or legacy JSON"""
    db_path = os.path.join(EXTENSION_PATH, 'wmd_data.db')
    if os.path.exists(db_path):
        return 'sqlite'
    return 'json'

def load_settings():
    if get_storage_backend() == 'sqlite':
        return SettingsRepository().get_all()
    else:
        # Legacy JSON loading
        with open(SETTINGS_FILE) as f:
            return json.load(f)
```

---

## File Structure After Migration

```
ComfyUI-Workflow-Models-Downloader/
├── database.py          # Database singleton and connection
├── repositories.py      # Repository classes
├── migrate_to_sqlite.py # Migration script
├── wmd_data.db          # SQLite database (new)
├── server.py            # Updated to use repositories
├── settings.json.bak    # Backup of old JSON (optional)
└── ...
```

---

## Implementation Order

```
Week 1: Foundation
├── Create database.py with schema
├── Create repositories.py with all repository classes
├── Add unit tests for repositories
└── Test with fresh database

Week 2: Migration
├── Create migrate_to_sqlite.py
├── Test migration with sample data
├── Add backward compatibility layer
└── Test fallback to JSON

Week 3: Integration
├── Update server.py to use repositories
├── Replace all JSON file operations
├── Test all endpoints
└── Performance testing

Week 4: Cleanup
├── Add auto-migration on startup
├── Remove deprecated JSON code
├── Update documentation
└── Release
```

---

## API Changes

None - all changes are internal. Existing endpoints work unchanged.

---

## Rollback Plan

1. Keep `.bak` files for 2 releases
2. Add `--use-json` CLI flag to force JSON mode
3. Include `migrate_to_json.py` reverse script

---

## Performance Comparison

| Operation | JSON (est.) | SQLite (est.) |
|-----------|-------------|---------------|
| Load all settings | 5-10ms | 1-2ms |
| Find model by hash | 100-500ms | 1-5ms |
| Add download history | 50-100ms | 1-2ms |
| Search metadata (10k entries) | 500ms+ | 5-20ms |
| Concurrent writes | Fails/corrupts | Works |

---

## New Capabilities Enabled

1. **Full-text search** on model names/descriptions
2. **Query by any field** (hash, source, type, date)
3. **Aggregations** (downloads per day, popular models)
4. **Expiring cache** with automatic cleanup
5. **Atomic batch operations**
6. **Database backup/restore**

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Keep `.bak` files, test extensively |
| SQLite lock contention | Use WAL mode, connection pooling |
| Larger binary size | sqlite3 is built into Python |
| Learning curve | Comprehensive documentation |
