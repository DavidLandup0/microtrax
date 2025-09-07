"""
Tests for backend services and API
"""
import json
import pytest
from pathlib import Path

from microtrax.backend.services.experiment_service import (
    load_experiments, extract_metrics, get_experiment_images
)
from microtrax.backend.services.plot_service import create_metric_plot
from microtrax.backend.app import create_app
from microtrax.constants import EXPERIMENTS_DIR


class TestExperimentLoader:

    def test_load_experiments_empty_dir(self, temp_logdir):
        """Test loading from empty directory"""
        experiments = load_experiments(temp_logdir)
        assert experiments == {}

    def test_load_experiments_with_data(self, temp_logdir, sample_experiment_data):
        """Test loading experiments with data"""
        # Create sample experiment file
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        experiments_dir.mkdir(parents=True, exist_ok=True)

        exp_file = experiments_dir / 'test_experiment.jsonl'
        with open(exp_file, 'w') as f:
            # Write metadata
            metadata = {"type": "metadata", **sample_experiment_data}
            f.write(json.dumps(metadata) + '\n')

            # Write log entries
            for i in range(3):
                log_entry = {
                    "type": "log",
                    "data": {"step": i, "loss": 1.0 - i * 0.1, "accuracy": i * 0.2}
                }
                f.write(json.dumps(log_entry) + '\n')

        experiments = load_experiments(temp_logdir)

        assert len(experiments) == 1
        assert 'test_experiment' in experiments

        exp_data = experiments['test_experiment']
        assert exp_data['metadata']['experiment_id'] == 'test_experiment'
        assert len(exp_data['logs']) == 3
        assert exp_data['logs'][0]['data']['step'] == 0

    def test_load_experiments_with_resources(self, temp_logdir, sample_experiment_data):
        """Test loading experiments with resource data"""
        # Create experiment file
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        experiments_dir.mkdir(parents=True, exist_ok=True)

        exp_file = experiments_dir / 'test_experiment.jsonl'
        with open(exp_file, 'w') as f:
            metadata = {"type": "metadata", **sample_experiment_data}
            f.write(json.dumps(metadata) + '\n')

        # Create resources file
        resources_dir = Path(temp_logdir) / 'resources'
        resources_dir.mkdir(exist_ok=True)

        resource_file = resources_dir / 'test_experiment_resources.jsonl'
        with open(resource_file, 'w') as f:
            resource_entry = {
                "timestamp": 1234567890.0,
                "cpu_percent": 50.0,
                "memory_percent": 60.0
            }
            f.write(json.dumps(resource_entry) + '\n')

        experiments = load_experiments(temp_logdir)

        exp_data = experiments['test_experiment']
        assert len(exp_data['resources']) == 1
        assert exp_data['resources'][0]['cpu_percent'] == 50.0


class TestMetricExtraction:

    def test_extract_metrics_basic(self):
        """Test basic metric extraction"""
        experiments = {
            'exp1': {
                'logs': [
                    {'data': {'step': 0, 'loss': 1.0, 'accuracy': 0.5}},
                    {'data': {'step': 1, 'loss': 0.8, 'lr': 0.01}}
                ],
                'resources': []
            }
        }

        metrics = extract_metrics(experiments)
        assert 'loss' in metrics
        assert 'accuracy' in metrics
        assert 'lr' in metrics
        assert 'step' not in metrics  # Should be excluded

    def test_extract_metrics_with_resources(self):
        """Test metric extraction including resources"""
        experiments = {
            'exp1': {
                'logs': [{'data': {'step': 0, 'loss': 1.0}}],
                'resources': [
                    {'timestamp': 123, 'cpu_percent': 50.0, 'memory_percent': 60.0},
                    {'timestamp': 124, 'gpu': [{'utilization_percent': 80.0}]}
                ]
            }
        }

        metrics = extract_metrics(experiments)
        assert 'loss' in metrics
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'gpu_utilization_percent' in metrics
        assert 'timestamp' not in metrics  # Should be excluded

    def test_extract_metrics_excludes_images(self):
        """Test that image keys are excluded from metrics"""
        experiments = {
            'exp1': {
                'logs': [
                    {'data': {'step': 0, 'loss': 1.0, '_images': [{'format': 'base64_png'}]}}
                ],
                'resources': []
            }
        }

        metrics = extract_metrics(experiments)
        assert 'loss' in metrics
        assert '_images' not in metrics


class TestImageExtraction:

    def test_get_experiment_images_empty(self):
        """Test getting images from experiment with no images"""
        experiments = {
            'exp1': {
                'logs': [{'data': {'step': 0, 'loss': 1.0}}]
            }
        }

        images = get_experiment_images(experiments, 'exp1')
        assert images == []

    def test_get_experiment_images_with_data(self):
        """Test getting images from experiment with image data"""
        experiments = {
            'exp1': {
                'logs': [
                    {
                        'data': {
                            'step': 0,
                            '_images': [
                                {
                                    'format': 'base64_png',
                                    'data': 'base64data',
                                    'label': 'test_image'
                                }
                            ]
                        }
                    }
                ]
            }
        }

        images = get_experiment_images(experiments, 'exp1')
        assert len(images) == 1
        assert images[0]['step'] == 0
        assert images[0]['data'] == 'base64data'
        assert images[0]['label'] == 'test_image'

    def test_get_experiment_images_nonexistent(self):
        """Test getting images from nonexistent experiment"""
        experiments = {}
        images = get_experiment_images(experiments, 'nonexistent')
        assert images == []


class TestPlotGenerator:

    def test_create_metric_plot_basic(self):
        """Test basic metric plot creation"""
        experiments = {
            'exp1': {
                'metadata': {'start_time_iso': '2023-01-01T12:00:00'},
                'logs': [
                    {'data': {'step': 0, 'loss': 1.0}},
                    {'data': {'step': 1, 'loss': 0.8}},
                    {'data': {'step': 2, 'loss': 0.6}}
                ],
                'resources': []
            }
        }

        plot_data = create_metric_plot(experiments, ['exp1'], 'loss')

        assert 'data' in plot_data
        assert 'layout' in plot_data
        assert plot_data['layout']['title']['text'] == 'loss'
        assert plot_data['layout']['xaxis']['title']['text'] == 'Step'

    def test_create_metric_plot_resource(self):
        """Test resource metric plot creation"""
        experiments = {
            'exp1': {
                'metadata': {'start_time': 1234567890.0},
                'logs': [],
                'resources': [
                    {'timestamp': 1234567890.0, 'cpu_percent': 50.0},
                    {'timestamp': 1234567950.0, 'cpu_percent': 60.0}  # 1 minute later
                ]
            }
        }

        plot_data = create_metric_plot(experiments, ['exp1'], 'cpu_percent')

        assert plot_data['layout']['title']['text'] == 'cpu_percent'
        assert plot_data['layout']['xaxis']['title']['text'] == 'Time (minutes)'

        # Check that timestamps were converted to relative minutes
        trace_data = plot_data['data'][0]
        assert trace_data['x'][0] == 0.0  # Start time
        assert abs(trace_data['x'][1] - 1.0) < 0.1  # ~1 minute later

    def test_create_metric_plot_multiple_experiments(self):
        """Test plot with multiple experiments"""
        experiments = {
            'exp1': {
                'metadata': {'start_time_iso': '2023-01-01T12:00:00'},
                'logs': [{'data': {'step': 0, 'loss': 1.0}}],
                'resources': []
            },
            'exp2': {
                'metadata': {'start_time_iso': '2023-01-01T13:00:00'},
                'logs': [{'data': {'step': 0, 'loss': 0.8}}],
                'resources': []
            }
        }

        plot_data = create_metric_plot(experiments, ['exp1', 'exp2'], 'loss')

        # Should have two traces
        assert len(plot_data['data']) == 2


class TestFastAPIApp:

    @pytest.fixture
    def app(self, temp_logdir):
        """Create test FastAPI app"""
        return create_app(temp_logdir)

    def test_app_creation(self, app):
        """Test that app is created successfully"""
        assert app.title == "microtrax Dashboard"
        assert hasattr(app.state, 'logdir')

    def test_root_endpoint(self, app):
        """Test root endpoint exists"""
        # Check that root route exists
        routes = [route.path for route in app.routes]
        assert "/" in routes
