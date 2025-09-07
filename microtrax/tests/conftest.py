"""
Test configuration and fixtures
"""
import pytest
import tempfile
import shutil
import numpy as np
import matplotlib.pyplot as plt


@pytest.fixture
def temp_logdir():
    """Create temporary directory for test logs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_experiment_data():
    """Sample experiment data for testing"""
    return {
        "experiment_id": "test_experiment",
        "start_time": 1234567890.0,
        "start_time_iso": "2009-02-13T23:31:30",
        "track_resources": True,
        "status": "running"
    }


@pytest.fixture
def sample_log_data():
    """Sample log data for testing"""
    return [
        {"step": 0, "loss": 1.0, "accuracy": 0.5},
        {"step": 1, "loss": 0.8, "accuracy": 0.6},
        {"step": 2, "loss": 0.6, "accuracy": 0.7}
    ]


@pytest.fixture
def sample_image():
    """Create a sample matplotlib figure for testing"""
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([1, 2, 3], [1, 4, 2])
    ax.set_title("Test Plot")
    return fig


@pytest.fixture
def sample_image_batch():
    """Create a sample image batch for testing"""
    return np.random.rand(4, 3, 32, 32)  # Batch of 4 RGB 32x32 images
