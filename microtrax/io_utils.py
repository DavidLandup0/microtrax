import json
import base64
import io
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np
import matplotlib.figure
from PIL import Image
import logging

def _dump_json(filepath, contents, mode='a'):
    with open(filepath, mode) as f:
        f.write(json.dumps(contents) + '\n')

def _ensure_dir(path: str) -> bool:
    """Ensure directory exists, return success status"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

def _buffer_to_base64(buffer):
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def __matplotlib_figure_to_base64(figure):
    buf = io.BytesIO()
    # Save to buffer
    figure.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    return _buffer_to_base64(buf)

def __ndarray_to_base64(ndarray):
     # Handle numpy arrays (height, width, channel) or (channel, height, width) format
    if ndarray.ndim == 3:
        if ndarray.shape[0] in [1, 3]:  # CHW format
            img = np.transpose(ndarray, (1, 2, 0))
        else:
            img = ndarray
    else:
        img = ndarray

    # Normalize to 0-255 if needed
    if img.dtype == np.float32 or img.dtype == np.float64:
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        else:
            img = img.astype(np.uint8)

    # Convert to PIL format for encoding
    if img.ndim == 3 and img.shape[2] == 1:
        img = img.squeeze(2)

    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    return _buffer_to_base64(buf)

def _image_to_base64(image_data) -> Optional[str]:
    """
    Convert image formats to base64 string.
    Accepts:
        - matplotlib.figure.Figure objects
        - CHW or HWC formatted numpy.ndarray
    """
    try:
        if isinstance(image_data, matplotlib.figure.Figure):
            return __matplotlib_figure_to_base64(image_data)

        elif isinstance(image_data, np.ndarray):
           return __ndarray_to_base64(image_data)

    except Exception as e:
        logging.warn(f"Exception occured while serializing image to base64: {str(e)}")
        return None

    return None

def _get_batch_size(batch_data, max_images: int) -> int:
    """Get the size of a batch, handling different data types"""
    if isinstance(batch_data, np.ndarray) and batch_data.ndim == 4:
        return min(batch_data.shape[0], max_images)
    elif isinstance(batch_data, (list, tuple)):
        return min(len(batch_data), max_images)
    return 0

def _get_image_at_index(batch_data, index: int):
    """Extract image at given index from batch data"""
    if isinstance(batch_data, np.ndarray) and batch_data.ndim == 4:
        return batch_data[index]
    elif isinstance(batch_data, (list, tuple)):
        return batch_data[index]
    return None

def _create_image_entry(img_b64: str, index: int) -> Dict[str, Any]:
    """Create a standardized image entry dictionary"""
    return {
        "format": "base64_png",
        "data": img_b64,
        "index": index
    }

def _add_label_to_entry(entry: Dict[str, Any], labels, index: int) -> None:
    """Add label to image entry if labels are provided"""
    if labels is None:
        return

    try:
        if isinstance(labels, (list, tuple, np.ndarray)) and index < len(labels):
            label = labels[index]
            if hasattr(label, 'item'):  # numpy scalar
                entry["label"] = label.item()
            else:
                entry["label"] = label
    except Exception as e:
        logging.warn(f"Exception occurred while adding labels for image batch: {str(e)}")

def _process_image_batch(batch_data, labels=None, max_images=16) -> List[Dict[str, Any]]:
    """Process a batch of images, optionally with labels"""
    try:
        processed_images = []
        batch_size = _get_batch_size(batch_data, max_images)

        for i in range(batch_size):
            img = _get_image_at_index(batch_data, i)
            if img is None:
                continue

            img_b64 = _image_to_base64(img)
            if img_b64:
                img_entry = _create_image_entry(img_b64, i)
                _add_label_to_entry(img_entry, labels, i)
                processed_images.append(img_entry)

        return processed_images

    except Exception:
        return []
