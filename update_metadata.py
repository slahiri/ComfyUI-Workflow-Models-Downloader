#!/usr/bin/env python3
"""
Update Metadata Script
Downloads the latest metadata files from ComfyUI Manager GitHub repository.

Usage:
    python update_metadata.py           # Update all metadata files
    python update_metadata.py --check   # Check for updates without downloading
"""

import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


# Metadata files to download from ComfyUI Manager
METADATA_FILES = {
    'extension-node-map.json': {
        'url': 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/extension-node-map.json',
        'description': 'Node to GitHub URL mappings'
    },
    'model-list.json': {
        'url': 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/model-list.json',
        'description': 'Model filename to type/directory mappings'
    },
    'custom-node-list.json': {
        'url': 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/custom-node-list.json',
        'description': 'Custom node reference information'
    }
}


def get_metadata_dir():
    """Get the metadata directory path"""
    return Path(__file__).parent / 'metadata'


def get_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    if not filepath.exists():
        return None

    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_content_hash(content):
    """Calculate MD5 hash of content bytes"""
    return hashlib.md5(content).hexdigest()


def download_file(url, timeout=30):
    """Download file content from URL"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (ComfyUI-Workflow-Models-Identifier)')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None


def format_size(size_bytes):
    """Format bytes to human readable size"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def update_metadata(check_only=False):
    """Update all metadata files from remote sources"""

    metadata_dir = get_metadata_dir()
    metadata_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("COMFYUI METADATA UPDATER")
    print("=" * 60)
    print(f"Source: ComfyUI-Manager GitHub Repository")
    print(f"Target: {metadata_dir}")
    print(f"Mode: {'Check only' if check_only else 'Update'}")
    print("=" * 60)
    print()

    results = {
        'updated': [],
        'unchanged': [],
        'errors': [],
        'new': []
    }

    for filename, info in METADATA_FILES.items():
        print(f"[{filename}]")
        print(f"  Description: {info['description']}")

        local_path = metadata_dir / filename
        local_hash = get_file_hash(local_path)
        local_exists = local_path.exists()

        if local_exists:
            local_size = local_path.stat().st_size
            local_mtime = datetime.fromtimestamp(local_path.stat().st_mtime)
            print(f"  Local: {format_size(local_size)}, modified {local_mtime.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  Local: Not found")

        print(f"  Downloading from: {info['url'][:60]}...")

        content = download_file(info['url'])

        if content is None:
            print(f"  Status: FAILED to download")
            results['errors'].append(filename)
            print()
            continue

        remote_hash = get_content_hash(content)
        remote_size = len(content)

        print(f"  Remote: {format_size(remote_size)}")

        if local_hash == remote_hash:
            print(f"  Status: UNCHANGED (hashes match)")
            results['unchanged'].append(filename)
        elif not local_exists:
            if not check_only:
                with open(local_path, 'wb') as f:
                    f.write(content)
                print(f"  Status: NEW file downloaded")
            else:
                print(f"  Status: NEW file available")
            results['new'].append(filename)
        else:
            if not check_only:
                with open(local_path, 'wb') as f:
                    f.write(content)
                print(f"  Status: UPDATED")
            else:
                print(f"  Status: UPDATE available")
            results['updated'].append(filename)

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if results['new']:
        print(f"New:       {len(results['new'])} file(s)")
        for f in results['new']:
            print(f"           - {f}")

    if results['updated']:
        print(f"Updated:   {len(results['updated'])} file(s)")
        for f in results['updated']:
            print(f"           - {f}")

    if results['unchanged']:
        print(f"Unchanged: {len(results['unchanged'])} file(s)")

    if results['errors']:
        print(f"Errors:    {len(results['errors'])} file(s)")
        for f in results['errors']:
            print(f"           - {f}")

    print("=" * 60)

    if check_only and (results['new'] or results['updated']):
        print("\nRun without --check to download updates.")

    return len(results['errors']) == 0


def show_metadata_stats():
    """Show statistics about current metadata files"""
    metadata_dir = get_metadata_dir()

    print("=" * 60)
    print("CURRENT METADATA FILES")
    print("=" * 60)

    if not metadata_dir.exists():
        print("Metadata directory not found. Run update first.")
        return

    for filename, info in METADATA_FILES.items():
        local_path = metadata_dir / filename
        print(f"\n[{filename}]")
        print(f"  Description: {info['description']}")

        if local_path.exists():
            size = local_path.stat().st_size
            mtime = datetime.fromtimestamp(local_path.stat().st_mtime)

            # Try to get entry count
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if filename == 'extension-node-map.json':
                    # Count total nodes across all extensions
                    total_nodes = sum(
                        len(v[0]) if isinstance(v, list) and len(v) > 0 and isinstance(v[0], list) else 0
                        for v in data.values()
                    )
                    print(f"  Extensions: {len(data)}")
                    print(f"  Total nodes: {total_nodes}")
                elif filename == 'model-list.json':
                    models = data.get('models', [])
                    print(f"  Models: {len(models)}")
                elif filename == 'custom-node-list.json':
                    nodes = data.get('custom_nodes', [])
                    print(f"  Custom nodes: {len(nodes)}")
            except:
                pass

            print(f"  Size: {format_size(size)}")
            print(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  Status: NOT FOUND")

    print()


def main():
    check_only = '--check' in sys.argv
    stats_only = '--stats' in sys.argv

    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        print("\nOptions:")
        print("  --check   Check for updates without downloading")
        print("  --stats   Show statistics about current metadata files")
        print("  --help    Show this help message")
        return

    if stats_only:
        show_metadata_stats()
        return

    success = update_metadata(check_only=check_only)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
