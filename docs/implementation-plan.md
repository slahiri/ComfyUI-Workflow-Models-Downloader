# Implementation Plan: ComfyUI Workflow Models Downloader

## Overview

This document outlines the implementation plan for features and improvements, ordered from high impact to low impact based on analysis of competitor repositories and open issues.

---

## Summary of All Open Issues

| # | Title | Key Features |
|---|-------|--------------|
| 10 | Bug: List JSON parse error | Fix for non-dict JSON files |
| 11 | Download safety & search accuracy | Temp files, filename parsing, hash verification |
| 12 | CivitAI image parsing, URN, HF scoring | CivitAI URL extraction, URN format, file scoring |
| 13 | Multi-environment compatibility | Jupyter, Colab, RunPod, cloud detection |
| 14 | R2/S3 Cloud Cache | Shared model storage across machines |
| 15 | Model Catalog/Registry | Curated list with verified paths |
| 16 | Smart Name Matching | Levenshtein, normalization, multi-strategy |
| 17 | Download Archive & Security | Deduplication, logging, path sanitization |
| 18 | Download Queue & Hash Search | Pause/resume, SHA256 search, WebSocket |

---

## Phase 1: Critical Fixes & Core Reliability

**Impact: Highest - Affects all users**

### 1.1 Bug Fix (Issue #10)
- **Status:** DONE
- Already fixed: List JSON parse error for non-dict workflow files

### 1.2 Download Safety (Issue #11) - IMPLEMENTED
- **Status:** DONE
- **Temp file downloads** - Download to `.tmp`, rename on success
- **Hash verification** - Verify SHA256 after download
- **Filename sanitization** - Clean unsafe characters
- **SafeDownloader class** - Atomic downloads with rollback
- **Implementation:** `security.py` - `SafeDownloader`, `calculate_file_hash()`, `verify_download_hash()`

### 1.3 Path Sanitization (Issue #17) - IMPLEMENTED
- **Status:** DONE
- **Security first** - Prevent directory traversal attacks
- **Validate paths** - Ensure downloads stay in models folder
- **Filename sanitization** - Remove unsafe characters, handle reserved names
- **URL validation** - Check for safe download sources
- **Implementation:** `security.py` - `sanitize_filename()`, `sanitize_path()`, `validate_download_path()`, `is_safe_url()`

---

## Phase 2: Search & Discovery Improvements

**Impact: High - Improves model finding success rate**

### 2.1 Smart Name Matching (Issue #16) - IMPLEMENTED
- **Status:** DONE (v1.9.0)
- **Name normalization** - Remove extensions, versions, common terms
- **Levenshtein + Jaccard** - Better similarity scoring (40%/60% weighted)
- **Multi-strategy search** - Try original, normalized, keywords, first keyword
- **Implementation:** `search_utils.py` - `normalize_model_name()`, `calculate_similarity()`, `generate_search_queries()`

### 2.2 CivitAI Improvements (Issue #12) - IMPLEMENTED
- **Status:** DONE (v1.9.0)
- **Image URL parsing** - Extract model ID from CivitAI image URLs
- **URN format support** - `urn:air:...:civitai:MODEL@VERSION` and `civitai:MODEL@VERSION`
- **API endpoint:** `/workflow-models/parse-civitai-url`
- **Implementation:** `search_utils.py` - `parse_civitai_image_url()`, `parse_civitai_urn()`

### 2.3 Hash-based Model Search (Issue #18) - EXISTING
- **Status:** Already existed
- **SHA256 calculation** - Hash local models
- **CivitAI hash API** - Find source by hash
- **API endpoint:** `/workflow-models/lookup-hash`

---

## Phase 3: Download Experience - IMPLEMENTED

**Impact: High - Major UX improvement**

### 3.1 Download Queue with Pause/Resume (Issue #18) - IMPLEMENTED
- **Status:** DONE
- **Task-based system** - Persistent queue saved to `download_queue.json`
- **HTTP Range resume** - Continue partial downloads with `.tmp` files
- **Queue management** - Pause, resume, cancel, priority
- **API endpoints:** `/workflow-models/queue/add`, `/queue/pause/{id}`, `/queue/resume/{id}`, `/queue/cancel/{id}`
- **Implementation:** `download_queue.py` - `DownloadQueue`, `DownloadTask`

### 3.2 Progress via WebSocket (Issue #18) - IMPLEMENTED
- **Status:** DONE
- **Real-time updates** - Progress bars, speed display, ETA
- **Status notifications** - Start, complete, error, pause events
- **Callback system** - Pluggable progress callbacks
- **Implementation:** `download_queue.py` - `WebSocketProgressBroadcaster`, `format_speed()`, `format_eta()`

### 3.3 Rich Debug Logging (Issue #17)
- **Emoji-based status** - Download, success, warning, error icons
- **Detailed progress** - Bytes, percentage, ETA

---

## Phase 4: Reliability & Deduplication - IMPLEMENTED

**Impact: Medium-High - Prevents wasted time/bandwidth**

### 4.1 Download Archive (Issue #17) - IMPLEMENTED
- **Status:** DONE
- **SQLite database** - Track all downloads with full history
- **Skip duplicates** - Don't re-download existing models
- **History tracking** - When, where, what source
- **API endpoints:** `/workflow-models/check-exists`, `/workflow-models/pre-download-check`
- **Implementation:** `reliability.py` - `check_already_downloaded()`, `should_skip_download()`

### 4.2 Disk Space Check (Issue #16) - IMPLEMENTED
- **Status:** DONE
- **Pre-download check** - Verify free space before download
- **Size estimation** - Estimate file size from URL or patterns
- **Warning system** - Alert when disk is >90% full or <5GB free
- **API endpoints:** `/workflow-models/disk-space`, `/workflow-models/check-disk-space`
- **Implementation:** `reliability.py` - `check_disk_space()`, `estimate_download_size()`

### 4.3 Duplicate Detection (Issue #16) - IMPLEMENTED
- **Status:** DONE
- **Hash-based detection** - Find exact duplicates via SHA256
- **Name-based detection** - Find similar files (different extensions/versions)
- **Cleanup recommendations** - Suggest files to delete (prefer .safetensors over .ckpt)
- **API endpoints:** `/workflow-models/duplicates`, `/workflow-models/cleanup-recommendations`
- **Implementation:** `reliability.py` - `find_duplicates_by_hash()`, `find_duplicates_by_name()`, `recommend_cleanup()`

---

## Phase 5: Enhanced Features

**Impact: Medium - Nice-to-have improvements**

### 5.1 Model Catalog/Registry (Issue #15) - IMPLEMENTED
- **Status:** DONE (v1.9.0)
- **Curated JSON** - `model_catalog.json` with 28 popular models
- **Fallback source** - Checked first before API search
- **API endpoint:** `/workflow-models/catalog-lookup`
- **Implementation:** `search_utils.py` - `lookup_catalog()`, `add_to_catalog()`

### 5.2 Model Description Files (Issue #18) - IMPLEMENTED
- **Status:** DONE (v1.9.0)
- **Markdown + YAML** - Save metadata alongside models as `.md` files
- **Trigger words** - Included in frontmatter
- **API endpoints:** `/workflow-models/save-description`, `/workflow-models/model-description`
- **Implementation:** `search_utils.py` - `save_model_description()`, `load_model_description()`

### 5.3 Video Preview Support (Issue #18)
- **MP4/WebM** - Animated previews
- **Priority order** - Video > animated image > static

---

## Phase 6: Platform & Security

**Impact: Medium - Specific use cases**

### 6.1 Multi-environment Support (Issue #13)
- **Environment detection** - Jupyter, Colab, RunPod, Vast.ai
- **Auto-configuration** - Token sources, paths
- **Headless mode** - CLI-only operation

### 6.2 Secure API Key Storage (Issue #18)
- **Encrypted storage** - Not plain text settings
- **Masked display** - `hf_a****xyz1`
- **Separate file** - `private.key`

---

## Phase 7: Advanced/Team Features

**Impact: Lower - Niche but powerful**

### 7.1 R2/S3 Cloud Cache (Issue #14)
- **S3-compatible storage** - R2, AWS, MinIO
- **Load order** - Local -> Cache -> Origin
- **Backfill** - Auto-upload to cache
- **Team sharing** - Multiple users, one cache

---

## Recommended Timeline

```
PHASE 1 (Week 1-2): Critical
├── 1.2 Temp file downloads + hash verification
└── 1.3 Path sanitization

PHASE 2 (Week 3-4): Search
├── 2.1 Name normalization + similarity scoring
├── 2.2 CivitAI image parsing + URN
└── 2.3 Hash-based search

PHASE 3 (Week 5-6): Downloads
├── 3.1 Download queue + pause/resume
├── 3.2 WebSocket progress
└── 3.3 Rich logging

PHASE 4 (Week 7): Reliability
├── 4.1 Download archive
├── 4.2 Disk space check
└── 4.3 Duplicate detection

PHASE 5 (Week 8): Enhanced
├── 5.1 Model catalog
├── 5.2 Description files
└── 5.3 Video previews

PHASE 6 (Week 9): Platform
├── 6.1 Multi-environment
└── 6.2 Secure key storage

PHASE 7 (Week 10+): Advanced
└── 7.1 R2/S3 cloud cache
```

---

## Quick Wins

These can be implemented anytime with minimal effort:

| Feature | Effort | Impact |
|---------|--------|--------|
| Rich debug logging | Low | Medium |
| Disk space check | Low | Medium |
| Name normalization | Low | High |
| Temp file downloads | Low | High |
| Path sanitization | Low | High (Security) |

---

## Competitor Analysis Sources

Features were inspired by analysis of these repositories:

| Repository | Key Features Adopted |
|------------|---------------------|
| [ciri/comfyui-model-downloader](https://github.com/ciri/comfyui-model-downloader) | Temp file downloads, filename extraction |
| [thaakeno/comfyui-universal-asset-downloader](https://github.com/thaakeno/comfyui-universal-asset-downloader) | CivitAI image parsing, URN format, Colab |
| [stavsap/comfyui-downloader](https://github.com/stavsap/comfyui-downloader) | Token source flexibility |
| [kycg/comfyui-Lora-auto-downloader](https://github.com/kycg/comfyui-Lora-auto-downloader) | R2/S3 cloud cache |
| [michaelgold/ComfyUI-HF-Model-Downloader](https://github.com/michaelgold/ComfyUI-HF-Model-Downloader) | License management, model catalog |
| [if-ai/ComfyUI-IF_AI_HFDownloaderNode](https://github.com/if-ai/ComfyUI-IF_AI_HFDownloaderNode) | HF collections, spaces, file exclusion |
| [mcrataobrabo/comfyui-smart-lora-downloader](https://github.com/mcrataobrabo/comfyui-smart-lora-downloader) | Smart name matching, multi-strategy search |
| [EricRollei/Download_Tools](https://github.com/EricRollei/Download_Tools) | Download archive, file organization |
| [hayden-fr/ComfyUI-Model-Manager](https://github.com/hayden-fr/ComfyUI-Model-Manager) | Download queue, hash search, WebSocket |

---

## Related GitHub Issues

- [#10 - Bug: List JSON parse error](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/10)
- [#11 - Download safety & search accuracy](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/11)
- [#12 - CivitAI image parsing, URN, HF scoring](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/12)
- [#13 - Multi-environment compatibility](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/13)
- [#14 - R2/S3 Cloud Cache](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/14)
- [#15 - Model Catalog/Registry](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/15)
- [#16 - Smart Name Matching](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/16)
- [#17 - Download Archive & Security](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/17)
- [#18 - Download Queue & Hash Search](https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader/issues/18)
