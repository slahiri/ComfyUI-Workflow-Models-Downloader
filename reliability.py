"""
Reliability Module: Download Archive, Disk Space Check, Duplicate Detection

Phase 4 features for improved reliability and resource management.
"""

import os
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Try to import folder_paths for ComfyUI model directories
try:
    import folder_paths
    HAS_FOLDER_PATHS = True
except ImportError:
    HAS_FOLDER_PATHS = False


# =============================================================================
# 4.1 DOWNLOAD ARCHIVE - Skip duplicates, track history
# =============================================================================

def check_file_exists(filename: str, directory: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a file already exists in the target directory.

    Returns:
        (exists, full_path) - Whether file exists and its full path if found
    """
    if not directory or not filename:
        return False, None

    target_path = os.path.join(directory, filename)
    if os.path.exists(target_path):
        return True, target_path

    return False, None


def check_already_downloaded(filename: str, directory: str = None) -> Dict:
    """
    Check if a model was already downloaded (in history or exists on disk).

    Returns:
        {
            'already_downloaded': bool,
            'exists_on_disk': bool,
            'in_history': bool,
            'history_entry': dict or None,
            'file_path': str or None,
            'file_size': int or None
        }
    """
    result = {
        'already_downloaded': False,
        'exists_on_disk': False,
        'in_history': False,
        'history_entry': None,
        'file_path': None,
        'file_size': None
    }

    # Check if file exists on disk
    if directory:
        exists, path = check_file_exists(filename, directory)
        if exists:
            result['exists_on_disk'] = True
            result['file_path'] = path
            result['already_downloaded'] = True
            try:
                result['file_size'] = os.path.getsize(path)
            except:
                pass

    # Check download history (try SQLite first, then fallback)
    try:
        from .storage import get_download_history
        history = get_download_history()
        for entry in history:
            if entry.get('filename') == filename and entry.get('status') == 'completed':
                result['in_history'] = True
                result['history_entry'] = entry
                result['already_downloaded'] = True
                break
    except:
        pass

    return result


def should_skip_download(filename: str, directory: str, force: bool = False) -> Tuple[bool, str]:
    """
    Determine if a download should be skipped.

    Args:
        filename: The filename to check
        directory: Target directory
        force: If True, don't skip even if exists

    Returns:
        (should_skip, reason) - Whether to skip and why
    """
    if force:
        return False, ""

    check = check_already_downloaded(filename, directory)

    if check['exists_on_disk']:
        size_str = ""
        if check['file_size']:
            size_mb = check['file_size'] / (1024 * 1024)
            size_str = f" ({size_mb:.1f} MB)"
        return True, f"File already exists{size_str}: {check['file_path']}"

    if check['in_history']:
        entry = check['history_entry']
        timestamp = entry.get('timestamp', entry.get('downloaded_at', 'unknown'))
        return True, f"Previously downloaded on {timestamp}"

    return False, ""


# =============================================================================
# 4.2 DISK SPACE CHECK - Verify free space before download
# =============================================================================

def get_disk_space(path: str) -> Dict:
    """
    Get disk space information for a path.

    Returns:
        {
            'total': int (bytes),
            'used': int (bytes),
            'free': int (bytes),
            'percent_used': float
        }
    """
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent_used': (used / total) * 100 if total > 0 else 0
        }
    except Exception as e:
        logging.error(f"[WMD] Error getting disk space: {e}")
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'percent_used': 0
        }


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} bytes"


def check_disk_space(directory: str, required_bytes: int, safety_margin: float = 1.1) -> Dict:
    """
    Check if there's enough disk space for a download.

    Args:
        directory: Target directory for download
        required_bytes: Size of file to download
        safety_margin: Multiply required by this (default 1.1 = 10% extra)

    Returns:
        {
            'has_space': bool,
            'required': int,
            'available': int,
            'required_str': str,
            'available_str': str,
            'warning': str or None
        }
    """
    # Ensure directory exists for disk check
    check_path = directory
    while not os.path.exists(check_path) and check_path:
        check_path = os.path.dirname(check_path)

    if not check_path:
        check_path = os.getcwd()

    space = get_disk_space(check_path)
    required_with_margin = int(required_bytes * safety_margin)

    result = {
        'has_space': space['free'] >= required_with_margin,
        'required': required_bytes,
        'available': space['free'],
        'required_str': format_bytes(required_bytes),
        'available_str': format_bytes(space['free']),
        'warning': None
    }

    if not result['has_space']:
        result['warning'] = f"Insufficient disk space. Need {result['required_str']} but only {result['available_str']} available."
    elif space['percent_used'] > 90:
        result['warning'] = f"Disk is {space['percent_used']:.1f}% full. Consider freeing up space."
    elif space['free'] < 5 * 1024 * 1024 * 1024:  # Less than 5GB free
        result['warning'] = f"Low disk space: only {result['available_str']} remaining."

    return result


def estimate_download_size(url: str = None, filename: str = None) -> Optional[int]:
    """
    Estimate download size from URL headers or filename patterns.

    Returns:
        Estimated size in bytes, or None if unknown
    """
    # Try to get size from URL headers
    if url:
        try:
            import requests
            response = requests.head(url, timeout=10, allow_redirects=True)
            if 'content-length' in response.headers:
                return int(response.headers['content-length'])
        except:
            pass

    # Estimate based on common model sizes by extension/name patterns
    if filename:
        filename_lower = filename.lower()

        # Checkpoint models (typically 2-7GB)
        if any(x in filename_lower for x in ['checkpoint', 'sd_xl', 'sdxl', 'flux']):
            return 6 * 1024 * 1024 * 1024  # 6GB estimate

        # LoRA models (typically 10-300MB)
        if 'lora' in filename_lower:
            return 150 * 1024 * 1024  # 150MB estimate

        # VAE (typically 300-800MB)
        if 'vae' in filename_lower:
            return 500 * 1024 * 1024  # 500MB estimate

        # ControlNet (typically 700MB-2GB)
        if 'controlnet' in filename_lower or 'control_' in filename_lower:
            return 1.5 * 1024 * 1024 * 1024  # 1.5GB estimate

        # CLIP/Text Encoders (typically 200MB-2GB)
        if 'clip' in filename_lower or 'text_encoder' in filename_lower:
            return 1 * 1024 * 1024 * 1024  # 1GB estimate

        # Upscale models (typically 60-200MB)
        if any(x in filename_lower for x in ['upscale', 'esrgan', 'realesrgan']):
            return 100 * 1024 * 1024  # 100MB estimate

        # Default for safetensors files
        if filename_lower.endswith('.safetensors'):
            return 2 * 1024 * 1024 * 1024  # 2GB estimate

        # Default for GGUF files (can be huge)
        if filename_lower.endswith('.gguf'):
            return 4 * 1024 * 1024 * 1024  # 4GB estimate

    return None


# =============================================================================
# 4.3 DUPLICATE DETECTION - Find duplicates by hash
# =============================================================================

def calculate_file_hash(filepath: str, algorithm: str = 'sha256',
                        chunk_size: int = 8192,
                        partial: bool = False) -> Optional[str]:
    """
    Calculate hash of a file.

    Args:
        filepath: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        chunk_size: Read chunk size
        partial: If True, only hash first 10MB for speed

    Returns:
        Hex digest string or None on error
    """
    if not os.path.exists(filepath):
        return None

    try:
        hasher = hashlib.new(algorithm)
        bytes_read = 0
        max_bytes = 10 * 1024 * 1024 if partial else float('inf')  # 10MB for partial

        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk or bytes_read >= max_bytes:
                    break
                hasher.update(chunk)
                bytes_read += len(chunk)

        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"[WMD] Error calculating hash for {filepath}: {e}")
        return None


def find_duplicates_by_hash(directory: str = None,
                            model_types: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Find duplicate models by comparing file hashes.

    Args:
        directory: Specific directory to scan, or None for all model dirs
        model_types: List of folder types to check (e.g., ['checkpoints', 'loras'])

    Returns:
        {
            'hash_value': [
                {'filename': str, 'path': str, 'size': int, 'type': str},
                ...
            ]
        }
        Only returns hashes with 2+ files (actual duplicates)
    """
    if model_types is None:
        model_types = ['checkpoints', 'loras', 'vae', 'controlnet', 'clip',
                       'embeddings', 'upscale_models']

    hash_map = {}  # hash -> list of files

    def scan_directory(path: str, folder_type: str):
        if not os.path.exists(path):
            return

        extensions = ('.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf')

        for root, dirs, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith(extensions):
                    filepath = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        # Use partial hash for speed on large files
                        partial = file_size > 100 * 1024 * 1024  # > 100MB
                        file_hash = calculate_file_hash(filepath, partial=partial)

                        if file_hash:
                            if file_hash not in hash_map:
                                hash_map[file_hash] = []
                            hash_map[file_hash].append({
                                'filename': filename,
                                'path': filepath,
                                'size': file_size,
                                'type': folder_type,
                                'size_str': format_bytes(file_size)
                            })
                    except Exception as e:
                        logging.debug(f"[WMD] Error scanning {filepath}: {e}")

    if directory:
        scan_directory(directory, 'custom')
    elif HAS_FOLDER_PATHS:
        for folder_type in model_types:
            try:
                paths = folder_paths.get_folder_paths(folder_type)
                for path in paths:
                    scan_directory(path, folder_type)
            except:
                pass

    # Filter to only duplicates (2+ files with same hash)
    duplicates = {h: files for h, files in hash_map.items() if len(files) > 1}

    return duplicates


def find_duplicates_by_name(model_types: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Find potential duplicates by similar filenames (different extensions).

    Returns:
        {
            'base_name': [
                {'filename': str, 'path': str, 'size': int, 'type': str, 'extension': str},
                ...
            ]
        }
    """
    if model_types is None:
        model_types = ['checkpoints', 'loras', 'vae', 'controlnet']

    name_map = {}  # base_name -> list of files

    def get_base_name(filename: str) -> str:
        """Get filename without extension and version numbers."""
        # Remove extension
        name = os.path.splitext(filename)[0]
        # Remove common version patterns
        import re
        name = re.sub(r'[-_]?v?\d+(\.\d+)*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[-_]?(fp16|fp32|q[48]_[01])$', '', name, flags=re.IGNORECASE)
        return name.lower()

    if HAS_FOLDER_PATHS:
        for folder_type in model_types:
            try:
                files = folder_paths.get_filename_list(folder_type)
                for filename in files:
                    base = get_base_name(filename)
                    full_path = folder_paths.get_full_path(folder_type, filename)

                    if base not in name_map:
                        name_map[base] = []

                    try:
                        size = os.path.getsize(full_path) if full_path else 0
                    except:
                        size = 0

                    name_map[base].append({
                        'filename': filename,
                        'path': full_path,
                        'size': size,
                        'size_str': format_bytes(size),
                        'type': folder_type,
                        'extension': os.path.splitext(filename)[1]
                    })
            except:
                pass

    # Filter to only potential duplicates
    duplicates = {n: files for n, files in name_map.items() if len(files) > 1}

    return duplicates


def get_duplicate_summary() -> Dict:
    """
    Get a summary of all potential duplicates.

    Returns:
        {
            'by_hash': {...},
            'by_name': {...},
            'total_wasted_space': int,
            'wasted_space_str': str,
            'duplicate_count': int
        }
    """
    by_hash = find_duplicates_by_hash()
    by_name = find_duplicates_by_name()

    # Calculate wasted space (all but one of each duplicate set)
    wasted = 0
    for files in by_hash.values():
        # Sort by size, keep largest, sum rest
        sorted_files = sorted(files, key=lambda x: x['size'], reverse=True)
        for f in sorted_files[1:]:
            wasted += f['size']

    return {
        'by_hash': by_hash,
        'by_name': by_name,
        'total_wasted_space': wasted,
        'wasted_space_str': format_bytes(wasted),
        'hash_duplicate_count': len(by_hash),
        'name_duplicate_count': len(by_name)
    }


# =============================================================================
# CLEANUP UTILITIES
# =============================================================================

def recommend_cleanup(duplicates: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Recommend files to delete from duplicate sets.

    Priority for keeping:
    1. .safetensors over .ckpt
    2. Larger file (more precision)
    3. More recently modified

    Returns:
        List of {'action': 'delete', 'path': str, 'reason': str, 'size': int}
    """
    recommendations = []

    for hash_val, files in duplicates.items():
        if len(files) < 2:
            continue

        def score_file(f):
            score = 0
            # Prefer .safetensors
            if f['filename'].lower().endswith('.safetensors'):
                score += 100
            # Prefer larger files
            score += f['size'] / (1024 * 1024 * 1024)  # Score per GB
            return score

        # Sort by score (highest = keep)
        sorted_files = sorted(files, key=score_file, reverse=True)
        keep = sorted_files[0]

        for f in sorted_files[1:]:
            reason = f"Duplicate of {keep['filename']}"
            if f['filename'].lower().endswith('.ckpt') and keep['filename'].lower().endswith('.safetensors'):
                reason += " (prefer .safetensors format)"

            recommendations.append({
                'action': 'delete',
                'path': f['path'],
                'filename': f['filename'],
                'size': f['size'],
                'size_str': f['size_str'],
                'reason': reason,
                'keep_instead': keep['filename']
            })

    return recommendations
