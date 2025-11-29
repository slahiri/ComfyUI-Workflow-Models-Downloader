"""
Search Utilities for Workflow Models Downloader

Features:
- Name normalization for better search matching
- Similarity scoring (Levenshtein + Jaccard)
- Multi-strategy search
- CivitAI image URL parsing
- Model catalog lookup
"""

import os
import re
import json
import logging
import hashlib
from typing import Optional, Tuple, List, Dict, Any


# =============================================================================
# NAME NORMALIZATION
# =============================================================================

def normalize_model_name(name: str) -> str:
    """
    Normalize model name for better search matching.

    Steps:
    1. Remove file extensions (.safetensors, .ckpt, .pt, .bin)
    2. Convert camelCase to spaces
    3. Split on numbers
    4. Convert separators to spaces
    5. Remove version patterns (v1, v1.5, SD1.5, XL)
    6. Remove common terms (lora, model, checkpoint, vae, unet)
    7. Clean up whitespace

    Examples:
        flux1-dev-fp8.safetensors -> flux dev fp8
        SDXL_Lightning_v2.0.ckpt -> Lightning
        dreamshaperXL_v21.safetensors -> dreamshaper
    """
    if not name:
        return ""

    # Remove file extensions
    name = re.sub(r'\.(safetensors|ckpt|pt|bin|pth|onnx|gguf)$', '', name, flags=re.IGNORECASE)

    # Convert camelCase to spaces (e.g., "dreamshaperXL" -> "dreamshaper XL")
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)

    # Split on numbers (e.g., "flux1dev" -> "flux 1 dev")
    name = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', name)
    name = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', name)

    # Convert separators to spaces
    name = re.sub(r'[_\-\.]+', ' ', name)

    # Remove version patterns (v1, v1.5, v2.0, etc.)
    name = re.sub(r'\bv\d+(\.\d+)?\b', '', name, flags=re.IGNORECASE)

    # Remove SD/SDXL version patterns
    name = re.sub(r'\b(sd|sdxl|xl)\s*\d*(\.\d+)?\b', '', name, flags=re.IGNORECASE)

    # Remove common quantization/precision terms
    name = re.sub(r'\b(fp16|fp32|fp8|bf16|e4m3fn|e5m2|scaled|pruned|emaonly)\b', '', name, flags=re.IGNORECASE)

    # Remove common model terms (keep them if they're the only content)
    terms_to_remove = r'\b(lora|loras|model|models|checkpoint|checkpoints|vae|unet|clip|embedding|embeddings)\b'
    cleaned = re.sub(terms_to_remove, '', name, flags=re.IGNORECASE)

    # Only use cleaned version if it still has meaningful content
    if cleaned.strip():
        name = cleaned

    # Clean up whitespace
    name = re.sub(r'\s+', ' ', name).strip().lower()

    return name


def extract_keywords(name: str, min_length: int = 3) -> List[str]:
    """
    Extract meaningful keywords from a model name.

    Args:
        name: Model name to extract keywords from
        min_length: Minimum keyword length to include

    Returns:
        List of keywords sorted by length (longest first)
    """
    normalized = normalize_model_name(name)
    words = normalized.split()

    # Filter by minimum length and remove common short terms
    stopwords = {'the', 'and', 'for', 'with', 'from', 'into'}
    keywords = [w for w in words if len(w) >= min_length and w not in stopwords]

    # Sort by length (longer keywords are usually more specific)
    keywords.sort(key=len, reverse=True)

    return keywords


# =============================================================================
# SIMILARITY SCORING
# =============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def jaccard_similarity(s1: str, s2: str) -> float:
    """Calculate Jaccard similarity between two strings based on word overlap."""
    words1 = set(s1.lower().split())
    words2 = set(s2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two model names.

    Uses a combination of:
    - Levenshtein distance (40% weight)
    - Jaccard word overlap (60% weight)

    Returns:
        Float between 0.0 and 1.0 (1.0 = identical)
    """
    # Normalize both names
    norm1 = normalize_model_name(name1)
    norm2 = normalize_model_name(name2)

    if not norm1 or not norm2:
        return 0.0

    # Exact match after normalization
    if norm1 == norm2:
        return 1.0

    # Containment check (one is substring of other)
    if norm1 in norm2 or norm2 in norm1:
        return 0.85

    # Levenshtein similarity
    max_len = max(len(norm1), len(norm2))
    distance = levenshtein_distance(norm1, norm2)
    lev_similarity = 1.0 - (distance / max_len) if max_len > 0 else 0.0

    # Jaccard word similarity
    word_similarity = jaccard_similarity(norm1, norm2)

    # Combined score (weighted)
    combined = (lev_similarity * 0.4) + (word_similarity * 0.6)

    return min(1.0, max(0.0, combined))


def find_best_match(target_name: str, candidates: List[Dict[str, Any]],
                    name_field: str = 'name', threshold: float = 0.3) -> Optional[Dict[str, Any]]:
    """
    Find the best matching candidate for a target name.

    Args:
        target_name: The name to match against
        candidates: List of candidate dicts with name field
        name_field: Key in candidate dict containing the name
        threshold: Minimum similarity score to consider a match

    Returns:
        Best matching candidate or None if no match above threshold
    """
    if not candidates:
        return None

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        candidate_name = candidate.get(name_field, '')
        if not candidate_name:
            continue

        score = calculate_similarity(target_name, candidate_name)

        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
            candidate['_similarity_score'] = score

    if best_match:
        logging.debug(f"[WMD] Best match for '{target_name}': '{best_match.get(name_field)}' (score: {best_score:.2f})")

    return best_match


# =============================================================================
# MULTI-STRATEGY SEARCH
# =============================================================================

def generate_search_queries(filename: str) -> List[Tuple[str, str]]:
    """
    Generate multiple search queries for a filename using different strategies.

    Returns:
        List of (strategy_name, query) tuples
    """
    queries = []

    # Strategy 1: Original filename (without extension)
    base_name = os.path.splitext(filename)[0]
    queries.append(('original', base_name))

    # Strategy 2: Normalized name
    normalized = normalize_model_name(filename)
    if normalized and normalized != base_name.lower():
        queries.append(('normalized', normalized))

    # Strategy 3: Top 3 keywords
    keywords = extract_keywords(filename)
    if keywords:
        top_keywords = ' '.join(keywords[:3])
        if top_keywords != normalized:
            queries.append(('keywords', top_keywords))

    # Strategy 4: First keyword only (if long enough)
    if keywords and len(keywords[0]) >= 5:
        first_keyword = keywords[0]
        if first_keyword != normalized and (first_keyword,) != tuple(top_keywords.split()):
            queries.append(('first_keyword', first_keyword))

    # Strategy 5: Remove all numbers and version info
    no_numbers = re.sub(r'\d+', '', base_name)
    no_numbers = re.sub(r'[_\-\.]+', ' ', no_numbers).strip()
    if no_numbers and len(no_numbers) >= 4 and no_numbers.lower() not in [q[1].lower() for q in queries]:
        queries.append(('no_numbers', no_numbers))

    return queries


# =============================================================================
# CIVITAI URL PARSING
# =============================================================================

def parse_civitai_image_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse CivitAI image URL to extract model and version IDs.

    Supports patterns:
    - https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/HASH/MODEL_ID-VERSION_ID/...
    - https://image.civitai.com/.../width=X/HASH/MODEL_ID-VERSION_ID.jpeg
    - https://civitai.com/images/IMAGE_ID (needs API lookup)

    Returns:
        (model_id, version_id) tuple or None if not parseable
    """
    if not url:
        return None

    # Pattern 1: image URL with MODEL_ID-VERSION_ID in path
    # Example: https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/abc123/12345-67890/...
    pattern1 = r'image\.civitai\.com/[^/]+/[^/]+/(\d+)-(\d+)'
    match = re.search(pattern1, url)
    if match:
        return match.group(1), match.group(2)

    # Pattern 2: image URL with MODEL_ID-VERSION_ID as filename
    # Example: .../12345-67890.jpeg
    pattern2 = r'/(\d+)-(\d+)\.(jpeg|jpg|png|webp)'
    match = re.search(pattern2, url)
    if match:
        return match.group(1), match.group(2)

    # Pattern 3: model page URL with version
    # Example: https://civitai.com/models/12345?modelVersionId=67890
    pattern3 = r'civitai\.com/models/(\d+)\?.*modelVersionId=(\d+)'
    match = re.search(pattern3, url)
    if match:
        return match.group(1), match.group(2)

    # Pattern 4: model page URL without version
    # Example: https://civitai.com/models/12345
    pattern4 = r'civitai\.com/models/(\d+)'
    match = re.search(pattern4, url)
    if match:
        return match.group(1), None

    return None


def civitai_image_to_model_url(image_url: str) -> Optional[str]:
    """
    Convert CivitAI image URL to model page URL.

    Returns:
        Model page URL or None if not parseable
    """
    result = parse_civitai_image_url(image_url)
    if not result:
        return None

    model_id, version_id = result
    if version_id:
        return f"https://civitai.com/models/{model_id}?modelVersionId={version_id}"
    else:
        return f"https://civitai.com/models/{model_id}"


def parse_civitai_urn(urn: str) -> Optional[Tuple[str, str]]:
    """
    Parse CivitAI URN format.

    Supports patterns:
    - urn:air:other:unknown:civitai:MODEL_ID@VERSION_ID
    - urn:air:MODEL_TYPE:BASE_MODEL:civitai:MODEL_ID@VERSION_ID
    - civitai:MODEL_ID@VERSION_ID (short form)

    Returns:
        (model_id, version_id) tuple or None if not valid
    """
    if not urn:
        return None

    # Full URN pattern
    full_pattern = r'^urn:air:[^:]+:[^:]+:civitai:(\d+)@(\d+)$'
    match = re.match(full_pattern, urn)
    if match:
        return match.group(1), match.group(2)

    # Short form: civitai:MODEL_ID@VERSION_ID
    short_pattern = r'^civitai:(\d+)@(\d+)$'
    match = re.match(short_pattern, urn)
    if match:
        return match.group(1), match.group(2)

    return None


def civitai_urn_to_download_url(urn: str) -> Optional[str]:
    """
    Convert CivitAI URN to download URL.

    Returns:
        Download URL or None if not valid
    """
    result = parse_civitai_urn(urn)
    if not result:
        return None

    model_id, version_id = result
    return f"https://civitai.com/api/download/models/{version_id}"


# =============================================================================
# MODEL CATALOG
# =============================================================================

# Path to model catalog file
CATALOG_FILE = os.path.join(os.path.dirname(__file__), 'model_catalog.json')

_catalog_cache = None


def load_model_catalog() -> Dict[str, Any]:
    """Load model catalog from JSON file."""
    global _catalog_cache

    if _catalog_cache is not None:
        return _catalog_cache

    try:
        if os.path.exists(CATALOG_FILE):
            with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
                _catalog_cache = json.load(f)
                logging.info(f"[WMD] Loaded model catalog with {len(_catalog_cache.get('models', []))} entries")
                return _catalog_cache
    except Exception as e:
        logging.error(f"[WMD] Error loading model catalog: {e}")

    _catalog_cache = {'models': [], 'version': '1.0.0'}
    return _catalog_cache


def save_model_catalog(catalog: Dict[str, Any]) -> bool:
    """Save model catalog to JSON file."""
    global _catalog_cache

    try:
        with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)
        _catalog_cache = catalog
        return True
    except Exception as e:
        logging.error(f"[WMD] Error saving model catalog: {e}")
        return False


def lookup_catalog(filename: str) -> Optional[Dict[str, Any]]:
    """
    Look up a model in the catalog by filename.

    Uses similarity matching if exact match not found.

    Returns:
        Catalog entry or None if not found
    """
    catalog = load_model_catalog()
    models = catalog.get('models', [])

    if not models:
        return None

    # Exact match first
    for model in models:
        if model.get('filename', '').lower() == filename.lower():
            logging.info(f"[WMD] Catalog exact match: {filename}")
            return model

    # Try normalized match
    normalized_target = normalize_model_name(filename)
    for model in models:
        normalized_catalog = normalize_model_name(model.get('filename', ''))
        if normalized_target == normalized_catalog:
            logging.info(f"[WMD] Catalog normalized match: {filename}")
            return model

    # Try similarity match
    best_match = find_best_match(filename, models, 'filename', threshold=0.7)
    if best_match:
        logging.info(f"[WMD] Catalog similarity match: {filename} -> {best_match.get('filename')}")
        return best_match

    return None


def add_to_catalog(entry: Dict[str, Any]) -> bool:
    """
    Add a model entry to the catalog.

    Required fields:
    - filename: Model filename
    - source: 'huggingface' or 'civitai'

    Optional fields:
    - repo_id: HuggingFace repo ID
    - hf_path: Path within HF repo
    - civitai_model_id: CivitAI model ID
    - civitai_version_id: CivitAI version ID
    - local_path: Suggested local path (e.g., 'loras/FLUX1')
    - model_type: checkpoints, loras, vae, etc.
    """
    catalog = load_model_catalog()
    models = catalog.get('models', [])

    # Remove existing entry with same filename
    filename = entry.get('filename', '')
    models = [m for m in models if m.get('filename', '').lower() != filename.lower()]

    # Add new entry
    models.append(entry)
    catalog['models'] = models

    return save_model_catalog(catalog)


# =============================================================================
# MODEL DESCRIPTION FILES
# =============================================================================

def get_description_path(model_path: str) -> str:
    """Get the path for a model's description file."""
    base_path = os.path.splitext(model_path)[0]
    return f"{base_path}.md"


def load_model_description(model_path: str) -> Optional[Dict[str, Any]]:
    """
    Load model description from .md file.

    Returns:
        Dict with 'frontmatter' (parsed YAML) and 'content' (markdown body)
        or None if file doesn't exist
    """
    desc_path = get_description_path(model_path)

    if not os.path.exists(desc_path):
        return None

    try:
        with open(desc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except:
                    pass
                body = parts[2].strip()

        return {
            'frontmatter': frontmatter,
            'content': body,
            'raw': content
        }
    except Exception as e:
        logging.error(f"[WMD] Error loading description for {model_path}: {e}")
        return None


def save_model_description(model_path: str, metadata: Dict[str, Any],
                          description: str = "") -> bool:
    """
    Save model description as .md file with YAML frontmatter.

    Args:
        model_path: Path to the model file
        metadata: Dict of metadata (website, author, triggerWords, etc.)
        description: Markdown body content

    Returns:
        True if saved successfully
    """
    desc_path = get_description_path(model_path)

    try:
        import yaml

        # Build frontmatter
        frontmatter = {
            'website': metadata.get('source', 'Unknown'),
            'modelPage': metadata.get('url', ''),
            'author': metadata.get('author', ''),
            'baseModel': metadata.get('base_model', ''),
            'triggerWords': metadata.get('trigger_words', []),
            'modelType': metadata.get('model_type', ''),
        }

        # Add hashes if available
        if metadata.get('sha256'):
            frontmatter['hashes'] = {'SHA256': metadata['sha256']}

        # Remove empty values
        frontmatter = {k: v for k, v in frontmatter.items() if v}

        # Build content
        parts = ['---']
        parts.append(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip())
        parts.append('---')
        parts.append('')

        # Trigger words section
        trigger_words = metadata.get('trigger_words', [])
        if trigger_words:
            parts.append('# Trigger Words')
            parts.append('')
            parts.append(', '.join(trigger_words))
            parts.append('')

        # Description section
        if description:
            parts.append('# Description')
            parts.append('')
            parts.append(description)

        content = '\n'.join(parts)

        with open(desc_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.info(f"[WMD] Saved description for {os.path.basename(model_path)}")
        return True

    except Exception as e:
        logging.error(f"[WMD] Error saving description for {model_path}: {e}")
        return False


# =============================================================================
# HASH UTILITIES
# =============================================================================

def calculate_file_hash(filepath: str, algorithm: str = 'sha256',
                       partial: bool = True, partial_size: int = 10 * 1024 * 1024) -> Optional[str]:
    """
    Calculate hash of a file.

    Args:
        filepath: Path to file
        algorithm: Hash algorithm ('sha256', 'md5', etc.)
        partial: If True, only hash first partial_size bytes (faster for large files)
        partial_size: Bytes to hash if partial=True (default 10MB)

    Returns:
        Hex digest string or None on error
    """
    if not os.path.exists(filepath):
        return None

    try:
        hasher = hashlib.new(algorithm)
        file_size = os.path.getsize(filepath)

        with open(filepath, 'rb') as f:
            if partial and file_size > partial_size:
                # Hash first chunk only for speed
                hasher.update(f.read(partial_size))
            else:
                # Hash entire file
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)

        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"[WMD] Error calculating hash for {filepath}: {e}")
        return None


def calculate_full_sha256(filepath: str) -> Optional[str]:
    """Calculate full SHA256 hash of a file (for CivitAI lookup)."""
    return calculate_file_hash(filepath, 'sha256', partial=False)
