"""
Security Module: Download Safety & Path Sanitization

Phase 1 security features for safe and secure downloads.
"""

import os
import re
import hashlib
import logging
import tempfile
from typing import Optional, Tuple
from pathlib import Path


# =============================================================================
# 1.2 DOWNLOAD SAFETY - Temp files, hash verification
# =============================================================================

class SafeDownloader:
    """
    Handles safe file downloads with:
    - Temp file downloads (.tmp extension)
    - Atomic rename on success
    - Hash verification
    - Cleanup on failure
    """

    def __init__(self, target_path: str, filename: str):
        """
        Initialize safe downloader.

        Args:
            target_path: Directory to save file
            filename: Final filename
        """
        self.target_path = target_path
        self.filename = sanitize_filename(filename)
        self.final_path = os.path.join(target_path, self.filename)
        self.temp_path = self.final_path + '.tmp'
        self.file_handle = None
        self.bytes_written = 0
        self.expected_hash = None
        self.expected_size = None

    def set_expected_hash(self, hash_value: str, algorithm: str = 'sha256'):
        """Set expected hash for verification."""
        self.expected_hash = hash_value
        self.hash_algorithm = algorithm

    def set_expected_size(self, size: int):
        """Set expected file size."""
        self.expected_size = size

    def open(self) -> 'SafeDownloader':
        """Open temp file for writing."""
        # Ensure directory exists
        os.makedirs(self.target_path, exist_ok=True)

        # Remove any existing temp file
        if os.path.exists(self.temp_path):
            try:
                os.remove(self.temp_path)
            except:
                pass

        self.file_handle = open(self.temp_path, 'wb')
        self.bytes_written = 0
        return self

    def write(self, chunk: bytes) -> int:
        """Write chunk to temp file."""
        if self.file_handle is None:
            raise RuntimeError("File not opened. Call open() first.")

        written = self.file_handle.write(chunk)
        self.bytes_written += written
        return written

    def close(self) -> None:
        """Close file handle without finalizing."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def abort(self) -> None:
        """Abort download and cleanup temp file."""
        self.close()
        if os.path.exists(self.temp_path):
            try:
                os.remove(self.temp_path)
                logging.info(f"[WMD] Cleaned up temp file: {self.temp_path}")
            except Exception as e:
                logging.warning(f"[WMD] Failed to cleanup temp file: {e}")

    def finalize(self, verify_hash: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Finalize download: verify and rename temp file to final.

        Args:
            verify_hash: Whether to verify hash if expected_hash is set

        Returns:
            (success, error_message)
        """
        self.close()

        # Verify file exists
        if not os.path.exists(self.temp_path):
            return False, "Temp file not found"

        # Verify size if expected
        if self.expected_size:
            actual_size = os.path.getsize(self.temp_path)
            if actual_size != self.expected_size:
                self.abort()
                return False, f"Size mismatch: expected {self.expected_size}, got {actual_size}"

        # Verify hash if expected
        if verify_hash and self.expected_hash:
            actual_hash = calculate_file_hash(self.temp_path, self.hash_algorithm)
            if actual_hash != self.expected_hash.lower():
                self.abort()
                return False, f"Hash mismatch: expected {self.expected_hash[:16]}..., got {actual_hash[:16]}..."

        # Remove existing final file if present
        if os.path.exists(self.final_path):
            try:
                os.remove(self.final_path)
            except Exception as e:
                self.abort()
                return False, f"Cannot overwrite existing file: {e}"

        # Atomic rename
        try:
            os.rename(self.temp_path, self.final_path)
            logging.info(f"[WMD] Download finalized: {self.filename}")
            return True, None
        except Exception as e:
            self.abort()
            return False, f"Failed to rename temp file: {e}"

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.abort()
        else:
            self.close()
        return False


def calculate_file_hash(filepath: str, algorithm: str = 'sha256',
                        chunk_size: int = 8192) -> Optional[str]:
    """Calculate hash of a file."""
    if not os.path.exists(filepath):
        return None

    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"[WMD] Hash calculation error: {e}")
        return None


def verify_download_hash(filepath: str, expected_hash: str,
                         algorithm: str = 'sha256') -> Tuple[bool, str]:
    """
    Verify file hash matches expected.

    Returns:
        (matches, actual_hash)
    """
    actual = calculate_file_hash(filepath, algorithm)
    if actual is None:
        return False, "Hash calculation failed"

    matches = actual.lower() == expected_hash.lower()
    return matches, actual


# =============================================================================
# 1.3 PATH SANITIZATION - Security validation
# =============================================================================

# Characters not allowed in filenames
UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Dangerous path components
DANGEROUS_COMPONENTS = {'..', '.', '~', '$'}

# Reserved Windows filenames
WINDOWS_RESERVED = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for the filesystem.

    - Removes unsafe characters
    - Prevents reserved names
    - Limits length
    - Preserves extension
    """
    if not filename:
        return "unnamed_model"

    # Get base name only (no path components)
    filename = os.path.basename(filename)

    # Split name and extension
    name, ext = os.path.splitext(filename)

    # Remove unsafe characters
    name = UNSAFE_CHARS.sub('_', name)
    ext = UNSAFE_CHARS.sub('_', ext)

    # Handle reserved Windows names
    name_upper = name.upper()
    if name_upper in WINDOWS_RESERVED or name_upper.split('.')[0] in WINDOWS_RESERVED:
        name = f"_{name}"

    # Remove leading/trailing spaces and dots
    name = name.strip(' .')

    # Handle empty name
    if not name:
        name = "unnamed_model"

    # Limit total length (255 is common max, leave room for extension)
    max_name_len = 200
    if len(name) > max_name_len:
        name = name[:max_name_len]

    return f"{name}{ext}"


def sanitize_path(path: str) -> str:
    """
    Sanitize a path to prevent directory traversal.

    - Removes dangerous components (.., ~, etc.)
    - Normalizes separators
    """
    if not path:
        return ""

    # Normalize separators
    path = path.replace('\\', '/').replace('//', '/')

    # Split into components
    parts = path.split('/')

    # Filter dangerous components
    safe_parts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part in DANGEROUS_COMPONENTS:
            logging.warning(f"[WMD] Removed dangerous path component: {part}")
            continue
        if part.startswith('$') or part.startswith('~'):
            logging.warning(f"[WMD] Removed dangerous path component: {part}")
            continue
        # Sanitize each component
        safe_parts.append(sanitize_filename(part) if '.' in part else UNSAFE_CHARS.sub('_', part))

    return '/'.join(safe_parts)


def validate_path_within_base(path: str, base_path: str) -> Tuple[bool, str]:
    """
    Validate that a path stays within a base directory.

    Args:
        path: Path to validate (can be relative or absolute)
        base_path: Base directory that path must be within

    Returns:
        (is_valid, resolved_path or error_message)
    """
    try:
        # Resolve both paths to absolute
        base_resolved = os.path.realpath(os.path.abspath(base_path))
        path_resolved = os.path.realpath(os.path.abspath(path))

        # Check if path is within base (or equal to base)
        # Use os.path.commonpath for proper comparison
        try:
            common = os.path.commonpath([base_resolved, path_resolved])
            if common == base_resolved:
                return True, path_resolved
        except ValueError:
            # Different drives on Windows
            pass

        return False, f"Path escapes base directory: {path}"

    except Exception as e:
        return False, f"Path validation error: {e}"


def validate_download_path(target_dir: str, filename: str,
                           models_base: str) -> Tuple[bool, str, str]:
    """
    Validate and sanitize a download destination.

    Args:
        target_dir: Relative target directory (e.g., "checkpoints")
        filename: Filename to download
        models_base: Base models directory

    Returns:
        (is_valid, sanitized_full_path, error_message)
    """
    # Sanitize inputs
    safe_dir = sanitize_path(target_dir)
    safe_filename = sanitize_filename(filename)

    # Build full path
    full_path = os.path.join(models_base, safe_dir, safe_filename)

    # Validate path stays within models directory
    is_valid, result = validate_path_within_base(full_path, models_base)

    if is_valid:
        return True, result, ""
    else:
        logging.error(f"[WMD] Invalid download path: {result}")
        return False, "", result


def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Basic URL safety check.

    Returns:
        (is_safe, reason)
    """
    if not url:
        return False, "Empty URL"

    # Must be HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        return False, "URL must be HTTP or HTTPS"

    # Check for suspicious patterns
    suspicious_patterns = [
        'file://',
        'javascript:',
        'data:',
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
    ]

    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            return False, f"Suspicious URL pattern: {pattern}"

    # Allowed domains for model downloads
    allowed_domains = [
        'huggingface.co',
        'civitai.com',
        'github.com',
        'raw.githubusercontent.com',
        'cdn-lfs.huggingface.co',
        'cdn-lfs-us-1.huggingface.co',
        'cdn-lfs-eu-1.huggingface.co',
        'cdn-lfs-asia-1.huggingface.co',
    ]

    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]

        # Check if host matches any allowed domain
        for domain in allowed_domains:
            if host == domain or host.endswith('.' + domain):
                return True, ""

        # Not in whitelist - warn but allow (user might have custom source)
        logging.warning(f"[WMD] URL from non-standard domain: {host}")
        return True, f"Non-standard domain: {host}"

    except Exception as e:
        return False, f"URL parsing error: {e}"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_temp_download_path(target_path: str, filename: str) -> str:
    """Get temp file path for download."""
    return os.path.join(target_path, sanitize_filename(filename) + '.tmp')


def cleanup_temp_files(directory: str) -> int:
    """
    Clean up orphaned .tmp files in a directory.

    Returns number of files cleaned.
    """
    cleaned = 0
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.tmp'):
                filepath = os.path.join(directory, filename)
                try:
                    # Only remove if older than 1 hour
                    import time
                    age = time.time() - os.path.getmtime(filepath)
                    if age > 3600:  # 1 hour
                        os.remove(filepath)
                        cleaned += 1
                        logging.info(f"[WMD] Cleaned up old temp file: {filename}")
                except:
                    pass
    except Exception as e:
        logging.error(f"[WMD] Temp file cleanup error: {e}")

    return cleaned
