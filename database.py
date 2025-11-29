"""
SQLite Database Layer for Workflow Models Downloader

Provides thread-safe database access with connection pooling.
"""

import sqlite3
import threading
import logging
import os
from contextlib import contextmanager
from typing import Any, Optional, List, Dict

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'wmd_data.db')

# Schema version for migrations
SCHEMA_VERSION = 1


class Database:
    """
    Thread-safe SQLite database singleton.

    Uses thread-local connections for safe concurrent access.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        self.db_path = db_path or DB_PATH
        self._local = threading.local()
        self._initialized = True
        self._init_schema()
        logging.info(f"[WMD] Database initialized: {self.db_path}")

    @property
    def conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def close(self):
        """Close thread-local connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"[WMD] Transaction failed: {e}")
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement."""
        try:
            return self.conn.execute(sql, params)
        except sqlite3.Error as e:
            logging.error(f"[WMD] SQL error: {e}\nQuery: {sql}\nParams: {params}")
            raise

    def executemany(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute SQL with multiple parameter sets."""
        try:
            return self.conn.executemany(sql, params_list)
        except sqlite3.Error as e:
            logging.error(f"[WMD] SQL error: {e}\nQuery: {sql}")
            raise

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute and fetch single row."""
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute and fetch all rows."""
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary."""
        if row is None:
            return None
        return dict(row)

    def rows_to_dicts(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Convert list of sqlite3.Row to list of dictionaries."""
        return [dict(row) for row in rows]

    def _init_schema(self):
        """Initialize database schema."""
        with self.transaction():
            # Schema version table
            self.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check current version
            row = self.fetchone("SELECT MAX(version) as ver FROM schema_version")
            current_version = row['ver'] if row and row['ver'] else 0

            if current_version < SCHEMA_VERSION:
                self._apply_schema()
                self.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
                logging.info(f"[WMD] Database schema updated to version {SCHEMA_VERSION}")

    def _apply_schema(self):
        """Apply database schema."""

        # Settings table
        self.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Download history
        self.execute("""
            CREATE TABLE IF NOT EXISTS download_history (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                directory TEXT,
                url TEXT,
                source TEXT,
                status TEXT NOT NULL,
                error TEXT,
                total_size INTEGER DEFAULT 0,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_history_filename
            ON download_history(filename)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_history_status
            ON download_history(status)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_history_date
            ON download_history(downloaded_at DESC)
        """)

        # Model metadata
        self.execute("""
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
                trigger_words TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_metadata_source
            ON model_metadata(source)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_metadata_hash
            ON model_metadata(sha256_hash)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_metadata_type
            ON model_metadata(model_type)
        """)

        # Model catalog (curated entries)
        self.execute("""
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
                protected INTEGER DEFAULT 0,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_source
            ON model_catalog(source)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_catalog_model_type
            ON model_catalog(model_type)
        """)

        # Search cache (Tavily, API results)
        self.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                result TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_cache_source
            ON search_cache(source)
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_cache_expires
            ON search_cache(expires_at)
        """)

        # Usage tracking
        self.execute("""
            CREATE TABLE IF NOT EXISTS usage_cache (
                filename TEXT PRIMARY KEY,
                directory TEXT,
                use_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_last_used
            ON usage_cache(last_used DESC)
        """)

        # Node metadata
        self.execute("""
            CREATE TABLE IF NOT EXISTS node_metadata (
                node_type TEXT PRIMARY KEY,
                input_fields TEXT,
                output_fields TEXT,
                category TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Model aliases
        self.execute("""
            CREATE TABLE IF NOT EXISTS model_aliases (
                alias TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                source TEXT
            )
        """)
        self.execute("""
            CREATE INDEX IF NOT EXISTS idx_aliases_canonical
            ON model_aliases(canonical_name)
        """)


# Convenience function to get database instance
def get_db() -> Database:
    """Get the database singleton instance."""
    return Database()
