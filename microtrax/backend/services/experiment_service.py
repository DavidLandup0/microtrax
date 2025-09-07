import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from microtrax.constants import EXPERIMENTS_DIR, RESOURCES_DIR

def load_experiments(logdir: str) -> Dict[str, Dict[str, Any]]:
    """Load all experiments from logdir"""
    experiments = {}
    experiments_dir = Path(logdir) / EXPERIMENTS_DIR

    if not experiments_dir.exists():
        return experiments

    for file_path in experiments_dir.glob('*.jsonl'):
        try:
            experiment_data = {'metadata': {}, 'logs': [], 'resources': []}

            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('type') == 'metadata':
                            # Merge metadata entries
                            experiment_data['metadata'].update(entry)
                        elif entry.get('type') == 'log':
                            experiment_data['logs'].append(entry)
                    except json.JSONDecodeError:
                        continue

            # Load resource data if available
            experiment_id = experiment_data['metadata'].get('experiment_id', file_path.stem)
            resource_file = Path(logdir) / RESOURCES_DIR / f'{experiment_id}_resources.jsonl'
            if resource_file.exists():
                with open(resource_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            experiment_data['resources'].append(entry)
                        except json.JSONDecodeError:
                            continue

            experiments[experiment_id] = experiment_data

        except Exception as e:
            logging.warn(f"Experiment {experiment_id} failed to load. Skipping. Cause: {e}")
            continue

    return experiments


def extract_metrics(experiments: Dict[str, Dict[str, Any]]) -> List[str]:
    """Extract all unique metric names from experiments"""
    metrics = set()
    for exp_data in experiments.values():
        # Extract metrics from logs
        for log_entry in exp_data['logs']:
            data = log_entry.get('data', {})
            for key in data.keys():
                if (key != 'step' and
                    key != '_images' and
                    key != '_error' and not key.endswith('_labels')):
                    metrics.add(key)

        # Extract metrics from resources
        for resource_entry in exp_data.get('resources', []):
            for key in resource_entry.keys():
                if key != 'timestamp':
                    if key == 'gpu':
                        # GPU data is a list, extract individual metrics
                        if resource_entry[key]:  # If GPU data exists
                            metrics.add('gpu_utilization_percent')
                            metrics.add('gpu_memory_percent')
                            metrics.add('gpu_memory_used_mb')
                    else:
                        metrics.add(key)

    return sorted(list(metrics))


def get_experiment_images(experiments: Dict[str, Dict[str, Any]], exp_id: str) -> List[Dict[str, Any]]:
    """Extract images from experiment logs"""
    if exp_id not in experiments:
        return []

    images = []
    exp_data = experiments[exp_id]

    for i, log_entry in enumerate(exp_data['logs']):
        data = log_entry.get('data', {})
        step = data.get('step', i)

        for key, value in data.items():
            if key == '_images':
                if isinstance(value, list):
                    # Batch of images
                    for j, img_data in enumerate(value):
                        if isinstance(img_data, dict) and img_data.get('format') == 'base64_png':
                            images.append({
                                'step': step,
                                'key': f'{key}[{j}]',
                                'data': img_data['data'],
                                'label': img_data.get('label', f'Image {j}')
                            })
                elif isinstance(value, dict) and value.get('format') == 'base64_png':
                    # Single image
                    images.append({
                        'step': step,
                        'key': key,
                        'data': value['data'],
                        'label': value.get('label', 'Image')
                    })

    return images
