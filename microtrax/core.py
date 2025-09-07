import json
import time
import uuid
import threading
import atexit
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from microtrax.constants import MTX_GLOBALDIR, EXPERIMENTS_DIR, RESOURCES_DIR

from microtrax.enums import ExperimentStatus
from microtrax.dashboard import run_dashboard
from microtrax.io_utils import _dump_json, _ensure_dir, _image_to_base64, _process_image_batch
import warnings

import numpy as np
import psutil
import logging

# Global state
_current_experiment: Optional['Experiment'] = None
_resource_tracker: Optional['ResourceTracker'] = None
_cleanup_registered = False

def _cleanup_on_exit():
    """Automatically finish any running experiment when Python exits"""
    global _current_experiment, _resource_tracker
    try:
        if _current_experiment:
            # Mark as interrupted rather than completed
            end_metadata = {
                "type": "metadata",
                "end_time": time.time(),
                "total_steps": _current_experiment.step_counter,
                "status": ExperimentStatus.INTERRUPTED.value
            }
            _current_experiment._append_to_log(end_metadata)
            _current_experiment = None

        if _resource_tracker:
            _resource_tracker.stop()
            _resource_tracker = None
    except Exception:
        pass  # Silent cleanup


def _recover_incomplete_experiments(logdir: str):
    """Find and recover any incomplete experiments in logdir"""
    try:
        experiments_dir = Path(logdir) / EXPERIMENTS_DIR
        if not experiments_dir.exists():
            return

        for file_path in experiments_dir.glob('*.jsonl'):
            try:
                # Read the last few lines to check status
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                if not lines:
                    continue

                # Check if last entry has completion metadata
                last_line = lines[-1].strip()
                if last_line:
                    try:
                        last_entry = json.loads(last_line)
                        if (last_entry.get('type') == 'metadata' and
                            last_entry.get('status') in [ExperimentStatus.COMPLETED.value, ExperimentStatus.INTERRUPTED.value]):
                            continue  # Already properly closed
                    except json.JSONDecodeError:
                        pass

                # Find experiment metadata to get step count
                experiment_id = file_path.stem
                step_count = 0

                for line in lines:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('type') == 'log':
                            step_count = max(step_count, entry.get('data', {}).get('step', 0) + 1)
                    except (json.JSONDecodeError, TypeError):
                        continue

                # Append completion metadata
                recovery_metadata = {
                    "type": "metadata",
                    "end_time": time.time(),
                    "total_steps": step_count,
                    "status": "recovered",
                    "recovery_note": "Experiment was incomplete, automatically recovered"
                }

                _dump_json(file_path, recovery_metadata, mode='a')

            except Exception as e:
                logging.warn(f"Incomplete experiment recovery failed: {str(e)}")
                continue  # No can do :(

    except Exception as e:
        logging.warn(f"Incomplete experiment recovery failed: {str(e)}")
        pass

class ExperimentContext:
    """Context manager for automatic experiment cleanup"""
    def __init__(self, logdir: Optional[str] = None, track_resources: bool = True, name: Optional[str] = None):
        self.logdir = logdir
        self.track_resources = track_resources
        self.name = name

    def __enter__(self):
        init(self.logdir, self.track_resources, self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always finish, even if there was an exception
        finish()
        # Don't suppress exceptions
        return False

def _safe_execute(func, *args, **kwargs):
    """Execute function with graceful error handling - avoids raising exceptions so we don't interrupt the outer call using microtrax."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        warnings.warn(f"microtrax: {func.__name__} failed - {str(e)}", UserWarning)
        return None

class Experiment:
    """
    Class to formalize an experiment (i.e. whatever that happens between mtx.init() and mtx.finish())
    """
    def __init__(self, experiment_id: str, logdir: str, track_resources: bool = False, name: Optional[str] = None):
        self.experiment_id = experiment_id
        self.name = name
        self.logdir = Path(logdir)
        self.experiments_dir = self.logdir / EXPERIMENTS_DIR
        self.track_resources = track_resources
        self.step_counter = 0
        self.start_time = time.time()
        self.has_images = False

        # Ensure directories exist
        _ensure_dir(str(self.experiments_dir))
        if track_resources:
            _ensure_dir(str(self.logdir / RESOURCES_DIR))

        self.log_file = self.experiments_dir / f"{experiment_id}.jsonl"

        # Write metadata header
        self._write_metadata()

    def _append_to_log(self, data: Dict[str, Any]):
        """Append data to log file with graceful error handling"""
        try:
            _dump_json(self.log_file, data, mode='a')
        except Exception as e:
            logging.warn(f"Exception occured while appending entry to log: {str(e)}")
            pass

    def _write_metadata(self):
        """Write experiment metadata header"""
        metadata = {
            "type": "metadata",
            "experiment_id": self.experiment_id,
            "name": self.name,
            "start_time": self.start_time,
            "start_time_iso": datetime.fromtimestamp(self.start_time).isoformat(),
            "track_resources": self.track_resources,
            "has_images": self.has_images,
            "status": ExperimentStatus.RUNNING.value
        }
        self._append_to_log(metadata)

    def log_entry(self, data: Dict[str, Any]):
        try:
            # Create log entry
            entry = {
                "type": "log",
                "timestamp": time.time(),
                "data": {}
            }

            # Handle step auto-increment
            if 'step' not in data:
                data['step'] = self.step_counter
                self.step_counter += 1
            else:
                self.step_counter = max(self.step_counter, data['step'] + 1)

            # Process each key-value pair - only handle regular metrics and special _images entries
            for key, value in data.items():
                # Handle regular data with NaN conversion for errors
                try:
                    # Ensure JSON serializable
                    if isinstance(value, np.ndarray):
                        if value.ndim == 0:  # scalar
                            entry["data"][key] = float(value)
                        else:
                            entry["data"][key] = value.tolist()
                    elif hasattr(value, 'item'):  # numpy scalars
                        entry["data"][key] = value.item()
                    else:
                        json.dumps(value)  # Test if serializable
                        entry["data"][key] = value
                except (TypeError, ValueError):
                    # Convert errors to NaN for charts
                    entry["data"][key] = float('nan')

            self._append_to_log(entry)

        except Exception as e:
            # Failure occured - create a step for the log, annotating the data as errored.
            logging.warn(f"Exception occured while creating log entry: {str(e)}")
            try:
                minimal_entry = {
                    "type": "log",
                    "timestamp": time.time(),
                    "data": {"step": data.get('step', self.step_counter), "_error": True}
                }
                self._append_to_log(minimal_entry)
            except Exception:
                logging.warn(f"Automatic logging recovery failed: {str(e)}")
                pass

    def _update_metadata_flag(self, key: str, value: Any):
        """Update a specific metadata field by appending new metadata entry"""
        metadata = {
            "type": "metadata",
            key: value
        }
        self._append_to_log(metadata)

    def finalize(self):
        """Finalize experiment with end metadata"""
        end_metadata = {
            "type": "metadata",
            "end_time": time.time(),
            "total_steps": self.step_counter,
            "status": ExperimentStatus.COMPLETED.value
        }
        self._append_to_log(end_metadata)

class ResourceTracker:
    """
    Class to formalize the automatic resource (CPU/GPU/memory) tracker.
    """
    def __init__(self, experiment_id: str, logdir: str):
        self.experiment_id = experiment_id
        self.logdir = Path(logdir)
        self.resource_file = self.logdir / RESOURCES_DIR / f"{experiment_id}_resources.jsonl"
        self.running = False
        self.thread = None

        # Check GPU availability
        self.has_gpu = False
        try:
            import nvidia_ml_py3 as nvml
            nvml.nvmlInit()
            self.gpu_count = nvml.nvmlDeviceGetCount()
            self.has_gpu = self.gpu_count > 0
        except Exception:
            pass

    def start(self):
        """Start resource monitoring thread"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop resource monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _monitor_loop(self, sample_rate=10):
        """Resource monitoring loop"""
        while self.running:
            try:
                resources = self._collect_resources()
                if resources:
                    _dump_json(self.resource_file, resources, mode='a')
                time.sleep(sample_rate)
            except Exception as e:
                logging.warn(f"Resource monitor loop failure {str(e)}")
                pass

    def _collect_resources(self) -> Optional[Dict[str, Any]]:
        """Collect current resource usage"""
        try:
            data = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024)
            }

            if self.has_gpu:
                try:
                    import nvidia_ml_py3 as nvml
                    gpu_data = []
                    for i in range(self.gpu_count):
                        handle = nvml.nvmlDeviceGetHandleByIndex(i)
                        util = nvml.nvmlDeviceGetUtilizationRates(handle)
                        memory = nvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_data.append({
                            "gpu_id": i,
                            "utilization_percent": util.gpu,
                            "memory_percent": (memory.used / memory.total) * 100,
                            "memory_used_mb": memory.used / (1024 * 1024)
                        })
                    data["gpu"] = gpu_data
                except Exception as e:
                    logging.warn(f"Resource collection failed: {str(e)}")
                    pass

            return data
        except Exception as e:
            logging.warn(f"Resource collection failed: {str(e)}")
            return None

def init(logdir: Optional[str] = None, track_resources: bool = True, name: Optional[str] = None):
    """
    Initialize an experiment in a `microtrax` 
    Uses default global logdir, or user-defined logdir.
    """
    global _current_experiment, _resource_tracker

    return _safe_execute(_init_impl, logdir, track_resources, name)

def _init_impl(logdir: Optional[str], track_resources: bool, name: Optional[str]):
    global _current_experiment, _resource_tracker, _cleanup_registered

    # Register cleanup handler on first use
    if not _cleanup_registered:
        atexit.register(_cleanup_on_exit)
        _cleanup_registered = True

    if logdir is None:
        logdir = MTX_GLOBALDIR

    _recover_incomplete_experiments(logdir)

    if _current_experiment:
        finish()

    # Generate unique experiment ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    experiment_id = f"experiment_{timestamp}_{short_id}"

    # Create experiment
    _current_experiment = Experiment(experiment_id, logdir, track_resources, name)

    # Start resource tracking if enabled
    if track_resources:
        _resource_tracker = ResourceTracker(experiment_id, logdir)
        _resource_tracker.start()

def log(*args, **kwargs):
    """
    Log dictionary. A set of key-value pairs to log in the 
    form of metrics and their values over time. Expects `step` as the main X-axis.

    Live-updates the data and dashboard.
    
    Usage:
        mtx.log({"step": 1, "loss": 0.5})  # Dictionary
        mtx.log(step=1, loss=0.5)          # Keyword arguments
    """
    # Handle both dict and kwargs forms
    if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
        # Called as mtx.log({"key": "value"})
        return _safe_execute(_log_impl, **args[0])
    elif len(args) == 0 and kwargs:
        # Called as mtx.log(key="value")
        return _safe_execute(_log_impl, **kwargs)
    else:
        warnings.warn("microtrax: log() expects either a dictionary or keyword arguments", UserWarning)
        return None

def _is_experiment_active():
    global _current_experiment
    if _current_experiment is None:
        warnings.warn("microtrax: No active experiment. Call mtx.init() first.", UserWarning)
        return

def _log_impl(**kwargs):
    _is_experiment_active()
    _current_experiment.log_entry(kwargs)

def log_images(images, step: Optional[int] = None, labels=None):
    """
    Log images separately from metrics.
    
    Args:
        images: Single image, list of images, or numpy batch (B,C,H,W)
        step: Step number (auto-incremented if not provided)
        labels: Optional labels for the images
    
    Usage:
        mtx.log_images(single_img, step=5)
        mtx.log_images([img1, img2], step=5, labels=["cat", "dog"])
        mtx.log_images(batch_tensor, step=5, labels=class_ids)
    """
    return _safe_execute(_log_images_impl, images, step, labels)

def _log_images_impl(images, step: Optional[int], labels):
    _is_experiment_active()

    # Create image log entry
    entry_data = {}
    if step is not None:
        entry_data['step'] = step

    # List of images or batch tensor
    if isinstance(images, (list, tuple)) or (isinstance(images, np.ndarray) and images.ndim == 4):
        # List of images
        processed_images = _process_image_batch(images, labels)
    else:
        # Single image
        img_b64 = _image_to_base64(images)
        if img_b64:
            processed_images = [{
                "format": "base64_png",
                "data": img_b64,
                "label": labels if isinstance(labels, (str, int, float)) else None
            }]
        else:
            processed_images = []

    if processed_images:
        entry_data['_images'] = processed_images  # Use _images to distinguish from metrics

        # Set has_images flag on first image log and update metadata
        if not _current_experiment.has_images:
            _current_experiment.has_images = True
            _current_experiment._update_metadata_flag('has_images', True)

    _current_experiment.log_entry(entry_data)

def finish():
    """
    Finalize current experiment in dir.
    This resets the global flag for current experiment so you can log onto a new file.
    """
    return _safe_execute(_finish_impl)

def _finish_impl():
    global _current_experiment, _resource_tracker

    if _current_experiment:
        _current_experiment.finalize()
        _current_experiment = None

    if _resource_tracker:
        _resource_tracker.stop()
        _resource_tracker = None

def serve(logdir: Optional[str] = None, port: int = 8080, host: str = "localhost"):
    """
    Serves the logbook on a dashboard.
    A logbook is a collection of experiments (JSON files in logdir).
    """
    return _safe_execute(run_dashboard, logdir, port, host)
