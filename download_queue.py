"""
Download Queue Module: Pause/Resume & WebSocket Progress

Phase 3 features for improved download experience.
"""

import os
import json
import time
import logging
import threading
import hashlib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import requests

# Try to import folder_paths for ComfyUI
try:
    import folder_paths
    HAS_FOLDER_PATHS = True
except ImportError:
    HAS_FOLDER_PATHS = False


class DownloadStatus(Enum):
    """Download status states."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a download task in the queue."""
    id: str
    url: str
    filename: str
    directory: str
    source: str = ""  # huggingface, civitai, direct
    status: str = "queued"
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: float = 0.0
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    completed_at: str = ""
    # Resume support
    supports_resume: bool = False
    resume_from: int = 0
    # Metadata
    hf_repo: str = ""
    hf_path: str = ""
    expected_hash: str = ""
    # Priority (lower = higher priority)
    priority: int = 100

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DownloadQueue:
    """
    Persistent download queue with pause/resume support.

    Features:
    - Priority queue
    - Pause/resume downloads
    - HTTP Range resume for partial downloads
    - Speed calculation
    - ETA estimation
    - WebSocket progress callbacks
    """

    def __init__(self, max_parallel: int = 3, models_dir: str = None):
        self.max_parallel = max_parallel
        self.models_dir = models_dir or (folder_paths.models_dir if HAS_FOLDER_PATHS else ".")

        # Task storage
        self.tasks: Dict[str, DownloadTask] = {}
        self.task_lock = threading.Lock()

        # Active downloads
        self.active_threads: Dict[str, threading.Thread] = {}
        self.cancelled: set = set()
        self.paused: set = set()

        # Callbacks for progress updates
        self.progress_callbacks: List[Callable[[DownloadTask], None]] = []

        # Speed tracking
        self.speed_samples: Dict[str, List[float]] = {}

        # Queue file for persistence
        self.queue_file = os.path.join(os.path.dirname(__file__), 'download_queue.json')
        self._load_queue()

    def _load_queue(self):
        """Load queue from disk."""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = DownloadTask(**task_data)
                        # Reset in-progress tasks to queued
                        if task.status == DownloadStatus.DOWNLOADING.value:
                            task.status = DownloadStatus.QUEUED.value
                        self.tasks[task.id] = task
                logging.info(f"[WMD] Loaded {len(self.tasks)} queued downloads")
        except Exception as e:
            logging.error(f"[WMD] Failed to load queue: {e}")

    def _save_queue(self):
        """Save queue to disk."""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                data = {
                    'tasks': [t.to_dict() for t in self.tasks.values()
                              if t.status not in [DownloadStatus.COMPLETED.value,
                                                   DownloadStatus.CANCELLED.value]]
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"[WMD] Failed to save queue: {e}")

    def add_progress_callback(self, callback: Callable[[DownloadTask], None]):
        """Add a callback for progress updates."""
        self.progress_callbacks.append(callback)

    def _notify_progress(self, task: DownloadTask):
        """Notify all callbacks of progress update."""
        for callback in self.progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                logging.error(f"[WMD] Progress callback error: {e}")

    def add_task(self, url: str, filename: str, directory: str,
                 source: str = "direct", priority: int = 100,
                 hf_repo: str = "", hf_path: str = "",
                 expected_hash: str = "") -> DownloadTask:
        """Add a download task to the queue."""
        # Generate unique ID
        task_id = hashlib.md5(f"{url}_{filename}_{time.time()}".encode()).hexdigest()[:12]

        task = DownloadTask(
            id=task_id,
            url=url,
            filename=filename,
            directory=directory,
            source=source,
            priority=priority,
            hf_repo=hf_repo,
            hf_path=hf_path,
            expected_hash=expected_hash
        )

        with self.task_lock:
            self.tasks[task_id] = task
            self._save_queue()

        logging.info(f"[WMD] Added to queue: {filename} (ID: {task_id})")
        self._notify_progress(task)
        self._process_queue()

        return task

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all tasks."""
        return list(self.tasks.values())

    def get_active_tasks(self) -> List[DownloadTask]:
        """Get currently downloading tasks."""
        return [t for t in self.tasks.values()
                if t.status == DownloadStatus.DOWNLOADING.value]

    def get_queued_tasks(self) -> List[DownloadTask]:
        """Get queued tasks sorted by priority."""
        queued = [t for t in self.tasks.values()
                  if t.status == DownloadStatus.QUEUED.value]
        return sorted(queued, key=lambda t: t.priority)

    def pause_task(self, task_id: str) -> bool:
        """Pause a downloading task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == DownloadStatus.DOWNLOADING.value:
            self.paused.add(task_id)
            logging.info(f"[WMD] Pausing download: {task.filename}")
            return True

        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == DownloadStatus.PAUSED.value:
            self.paused.discard(task_id)
            task.status = DownloadStatus.QUEUED.value
            self._notify_progress(task)
            self._process_queue()
            logging.info(f"[WMD] Resumed download: {task.filename}")
            return True

        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in [DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value]:
            self.cancelled.add(task_id)
            task.status = DownloadStatus.CANCELLED.value
            self._save_queue()
            self._notify_progress(task)
            logging.info(f"[WMD] Cancelled download: {task.filename}")
            return True

        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a completed/cancelled/failed task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in [DownloadStatus.COMPLETED.value,
                               DownloadStatus.CANCELLED.value,
                               DownloadStatus.FAILED.value]:
                del self.tasks[task_id]
                self._save_queue()
                return True
        return False

    def clear_completed(self):
        """Remove all completed/cancelled/failed tasks."""
        to_remove = [tid for tid, task in self.tasks.items()
                     if task.status in [DownloadStatus.COMPLETED.value,
                                        DownloadStatus.CANCELLED.value,
                                        DownloadStatus.FAILED.value]]
        for tid in to_remove:
            del self.tasks[tid]
        self._save_queue()

    def _process_queue(self):
        """Process queue and start downloads if capacity available."""
        with self.task_lock:
            active_count = len([t for t in self.tasks.values()
                                if t.status == DownloadStatus.DOWNLOADING.value])

            if active_count >= self.max_parallel:
                return

            # Get next queued tasks
            queued = self.get_queued_tasks()
            slots_available = self.max_parallel - active_count

            for task in queued[:slots_available]:
                self._start_download(task)

    def _start_download(self, task: DownloadTask):
        """Start downloading a task in a background thread."""
        task.status = DownloadStatus.DOWNLOADING.value
        task.started_at = datetime.now().isoformat()
        self._notify_progress(task)

        thread = threading.Thread(
            target=self._download_worker,
            args=(task,),
            daemon=True
        )
        self.active_threads[task.id] = thread
        thread.start()

    def _download_worker(self, task: DownloadTask):
        """Worker thread for downloading."""
        try:
            from . import security

            # Build full target path
            target_path = os.path.join(self.models_dir, task.directory)
            os.makedirs(target_path, exist_ok=True)

            # Validate path
            is_valid, safe_path, error = security.validate_download_path(
                task.directory, task.filename, self.models_dir
            )
            if not is_valid:
                raise ValueError(f"Invalid path: {error}")

            # Prepare headers
            headers = self._get_headers(task)

            # Check if resume is supported
            resume_byte = 0
            temp_path = os.path.join(target_path, task.filename + '.tmp')

            if os.path.exists(temp_path):
                resume_byte = os.path.getsize(temp_path)
                if resume_byte > 0:
                    # Check if server supports range requests
                    head_resp = requests.head(task.url, headers=headers, timeout=10, allow_redirects=True)
                    if head_resp.headers.get('Accept-Ranges') == 'bytes':
                        headers['Range'] = f'bytes={resume_byte}-'
                        task.supports_resume = True
                        task.resume_from = resume_byte
                        logging.info(f"[WMD] Resuming from byte {resume_byte}")
                    else:
                        resume_byte = 0

            # Start download
            response = requests.get(
                task.url,
                stream=True,
                timeout=30,
                allow_redirects=True,
                headers=headers
            )
            response.raise_for_status()

            # Get total size
            content_length = response.headers.get('content-length')
            if content_length:
                if response.status_code == 206:  # Partial content
                    task.total_bytes = resume_byte + int(content_length)
                else:
                    task.total_bytes = int(content_length)
                    resume_byte = 0  # Server didn't honor range request

            task.downloaded_bytes = resume_byte

            # Speed tracking
            start_time = time.time()
            last_update = start_time
            last_bytes = resume_byte

            # Download to temp file
            mode = 'ab' if resume_byte > 0 else 'wb'
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Check for pause/cancel
                    if task.id in self.cancelled:
                        raise InterruptedError("Download cancelled")

                    if task.id in self.paused:
                        task.status = DownloadStatus.PAUSED.value
                        self._notify_progress(task)
                        self._save_queue()
                        return

                    if chunk:
                        f.write(chunk)
                        task.downloaded_bytes += len(chunk)

                        # Update progress
                        if task.total_bytes > 0:
                            task.progress = (task.downloaded_bytes / task.total_bytes) * 100

                        # Calculate speed (every 0.5 seconds)
                        now = time.time()
                        if now - last_update >= 0.5:
                            bytes_delta = task.downloaded_bytes - last_bytes
                            time_delta = now - last_update

                            task.speed_bps = bytes_delta / time_delta

                            # ETA
                            if task.speed_bps > 0 and task.total_bytes > 0:
                                remaining = task.total_bytes - task.downloaded_bytes
                                task.eta_seconds = remaining / task.speed_bps

                            last_update = now
                            last_bytes = task.downloaded_bytes

                            self._notify_progress(task)

            # Verify hash if expected
            if task.expected_hash:
                actual_hash = security.calculate_file_hash(temp_path)
                if actual_hash.lower() != task.expected_hash.lower():
                    os.remove(temp_path)
                    raise ValueError(f"Hash mismatch: expected {task.expected_hash[:16]}...")

            # Rename temp to final
            final_path = os.path.join(target_path, task.filename)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)

            # Success
            task.status = DownloadStatus.COMPLETED.value
            task.completed_at = datetime.now().isoformat()
            task.progress = 100
            self._notify_progress(task)
            self._save_queue()

            logging.info(f"[WMD] Download completed: {task.filename}")

            # Add to download history
            try:
                from . import storage
                storage.add_to_download_history({
                    'id': task.id,
                    'filename': task.filename,
                    'directory': task.directory,
                    'url': task.url,
                    'source': task.source,
                    'status': 'completed',
                    'total_size': task.total_bytes
                })
            except:
                pass

        except InterruptedError:
            task.status = DownloadStatus.CANCELLED.value
            self._notify_progress(task)
            self._save_queue()
            # Cleanup temp file
            try:
                temp_path = os.path.join(self.models_dir, task.directory, task.filename + '.tmp')
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

        except Exception as e:
            task.status = DownloadStatus.FAILED.value
            task.error = str(e)
            self._notify_progress(task)
            self._save_queue()
            logging.error(f"[WMD] Download failed: {task.filename} - {e}")

        finally:
            self.cancelled.discard(task.id)
            self.paused.discard(task.id)
            if task.id in self.active_threads:
                del self.active_threads[task.id]

            # Process next in queue
            self._process_queue()

    def _get_headers(self, task: DownloadTask) -> Dict[str, str]:
        """Get appropriate headers for download."""
        headers = {}

        if 'civitai.com' in task.url:
            try:
                from . import server
                civitai_key = server.get_civitai_api_key()
                if civitai_key:
                    # CivitAI uses token as query param, add to URL
                    if '?' in task.url:
                        task.url = f"{task.url}&token={civitai_key}"
                    else:
                        task.url = f"{task.url}?token={civitai_key}"
            except:
                pass

        elif 'huggingface.co' in task.url:
            try:
                from . import server
                hf_token = server.get_huggingface_token()
                if hf_token:
                    headers['Authorization'] = f'Bearer {hf_token}'
            except:
                pass

        return headers


# Global queue instance
_queue_instance: Optional[DownloadQueue] = None
_queue_lock = threading.Lock()


def get_queue() -> DownloadQueue:
    """Get the global download queue instance."""
    global _queue_instance
    if _queue_instance is None:
        with _queue_lock:
            if _queue_instance is None:
                _queue_instance = DownloadQueue()
    return _queue_instance


# =============================================================================
# 3.2 WEBSOCKET PROGRESS
# =============================================================================

class WebSocketProgressBroadcaster:
    """
    Broadcasts download progress to WebSocket clients.

    Integrates with ComfyUI's existing WebSocket infrastructure.
    """

    def __init__(self):
        self.clients: List[Any] = []
        self.lock = threading.Lock()

    def add_client(self, ws):
        """Add a WebSocket client."""
        with self.lock:
            self.clients.append(ws)

    def remove_client(self, ws):
        """Remove a WebSocket client."""
        with self.lock:
            if ws in self.clients:
                self.clients.remove(ws)

    def broadcast(self, task: DownloadTask):
        """Broadcast task progress to all clients."""
        message = {
            'type': 'wmd_download_progress',
            'data': {
                'id': task.id,
                'filename': task.filename,
                'status': task.status,
                'progress': task.progress,
                'downloaded_bytes': task.downloaded_bytes,
                'total_bytes': task.total_bytes,
                'speed_bps': task.speed_bps,
                'eta_seconds': task.eta_seconds,
                'error': task.error
            }
        }

        with self.lock:
            dead_clients = []
            for client in self.clients:
                try:
                    # Async send - depends on ComfyUI's WebSocket implementation
                    if hasattr(client, 'send_json'):
                        client.send_json(message)
                    elif hasattr(client, 'send'):
                        client.send(json.dumps(message))
                except Exception as e:
                    logging.debug(f"[WMD] WebSocket send error: {e}")
                    dead_clients.append(client)

            # Cleanup dead clients
            for client in dead_clients:
                self.clients.remove(client)


# Global broadcaster
_broadcaster: Optional[WebSocketProgressBroadcaster] = None


def get_broadcaster() -> WebSocketProgressBroadcaster:
    """Get the global WebSocket broadcaster."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = WebSocketProgressBroadcaster()

        # Connect to queue
        queue = get_queue()
        queue.add_progress_callback(_broadcaster.broadcast)

    return _broadcaster


def format_speed(bps: float) -> str:
    """Format bytes per second to human readable."""
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    elif bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps:.0f} B/s"


def format_eta(seconds: float) -> str:
    """Format ETA seconds to human readable."""
    if seconds <= 0:
        return "calculating..."
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    hours = int(seconds / 3600)
    mins = int((seconds % 3600) / 60)
    return f"{hours}h {mins}m"
