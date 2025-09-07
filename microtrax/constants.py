import os

MTX_GLOBALDIR_NAME = "~/.microtrax"
MTX_GLOBALDIR = os.path.expanduser(MTX_GLOBALDIR_NAME)

# Directory names
EXPERIMENTS_DIR = "experiments"
RESOURCES_DIR = "resources"

# Metric lists
RESOURCE_METRICS = [
    'cpu_percent',
    'memory_percent',
    'memory_used_mb',
    'gpu_utilization_percent',
    'gpu_memory_percent',
    'gpu_memory_used_mb'
]
