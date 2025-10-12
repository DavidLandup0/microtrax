import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from microtrax.constants import TEXT_DIR


def load_text_data(logdir: str, experiment_id: str) -> List[Dict[str, Any]]:
    """Load text data for a specific experiment"""
    text_entries = []
    text_file = Path(logdir) / TEXT_DIR / f'{experiment_id}_text.jsonl'

    if not text_file.exists():
        return text_entries

    try:
        with open(text_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('type') == 'text':
                        text_entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logging.warn(f"Failed to load text data for {experiment_id}: {e}")

    return text_entries
