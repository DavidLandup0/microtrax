"""
Tests for core microtrax functionality
"""
import json
import pytest
from pathlib import Path
import matplotlib.pyplot as plt

import microtrax as mtx
import microtrax.core as core
from microtrax.enums import ExperimentStatus
from microtrax.constants import EXPERIMENTS_DIR, RESOURCES_DIR


class TestExperimentBasics:

    def test_init_creates_experiment(self, temp_logdir):
        """Test that init creates an experiment"""
        mtx.init(temp_logdir)
        assert core._current_experiment is not None
        assert core._current_experiment.logdir == Path(temp_logdir)
        mtx.finish()

    def test_init_creates_directories(self, temp_logdir):
        """Test that init creates necessary directories"""
        mtx.init(temp_logdir)

        logdir_path = Path(temp_logdir)
        assert (logdir_path / EXPERIMENTS_DIR).exists()
        assert (logdir_path / RESOURCES_DIR).exists()

        mtx.finish()

    def test_multiple_experiments_handled_gracefully(self, temp_logdir):
        """Test that multiple init calls are handled gracefully"""
        mtx.init(temp_logdir)
        first_exp_id = core._current_experiment.experiment_id

        # Second init should finish first experiment and start new one
        mtx.init(temp_logdir)
        second_exp_id = core._current_experiment.experiment_id

        # Should have different experiment IDs
        assert first_exp_id != second_exp_id

        mtx.finish()


class TestLogging:

    def test_log_basic_metrics(self, temp_logdir, sample_log_data):
        """Test basic metric logging"""
        mtx.init(temp_logdir)

        for data in sample_log_data:
            mtx.log(data)

        # Check log file was created
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))
        assert len(log_files) == 1

        # Check log contents
        with open(log_files[0], 'r') as f:
            lines = f.readlines()

        # Should have metadata + 3 log entries
        assert len(lines) >= 4

        # Check first line is metadata
        metadata = json.loads(lines[0])
        assert metadata['type'] == 'metadata'
        assert metadata['status'] == ExperimentStatus.RUNNING.value

        # Check log entries
        for i, line in enumerate(lines[1:4]):
            log_entry = json.loads(line)
            assert log_entry['type'] == 'log'
            assert log_entry['data']['step'] == i
            assert 'loss' in log_entry['data']
            assert 'accuracy' in log_entry['data']

        mtx.finish()

    def test_log_auto_step_increment(self, temp_logdir):
        """Test automatic step increment"""
        mtx.init(temp_logdir)

        # Log without specifying step
        mtx.log({"loss": 1.0})
        mtx.log({"loss": 0.8})
        mtx.log({"loss": 0.6})

        # Check steps were auto-incremented
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))

        with open(log_files[0], 'r') as f:
            lines = f.readlines()[1:]  # Skip metadata

        for i, line in enumerate(lines):
            log_entry = json.loads(line)
            assert log_entry['data']['step'] == i

        mtx.finish()

    def test_log_images_single(self, temp_logdir, sample_image):
        """Test logging single image"""
        mtx.init(temp_logdir)

        mtx.log_images(sample_image, step=0, labels="test_plot")

        # Check log file contains image data
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))

        with open(log_files[0], 'r') as f:
            lines = f.readlines()

        # Find image log entry
        image_entry = None
        for line in lines:
            entry = json.loads(line)
            if entry.get('type') == 'log' and '_images' in entry.get('data', {}):
                image_entry = entry
                break

        assert image_entry is not None
        assert 'step' in image_entry['data']
        assert '_images' in image_entry['data']
        assert len(image_entry['data']['_images']) == 1
        assert image_entry['data']['_images'][0]['format'] == 'base64_png'
        assert 'data' in image_entry['data']['_images'][0]

        plt.close(sample_image)
        mtx.finish()

    def test_log_images_batch(self, temp_logdir, sample_image_batch):
        """Test logging image batch"""
        mtx.init(temp_logdir)

        labels = ["img1", "img2", "img3", "img4"]
        mtx.log_images(sample_image_batch, step=0, labels=labels)

        # Check log file contains batch image data
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))

        with open(log_files[0], 'r') as f:
            lines = f.readlines()

        # Find image log entry
        image_entry = None
        for line in lines:
            entry = json.loads(line)
            if entry.get('type') == 'log' and '_images' in entry.get('data', {}):
                image_entry = entry
                break

        assert image_entry is not None
        assert len(image_entry['data']['_images']) == 4

        for i, img_data in enumerate(image_entry['data']['_images']):
            assert img_data['format'] == 'base64_png'
            assert img_data['label'] == labels[i]
            assert img_data['index'] == i

        mtx.finish()

    def test_log_nan_handling(self, temp_logdir):
        """Test that NaN values are handled gracefully"""
        mtx.init(temp_logdir)

        # Log some problematic values
        mtx.log({"loss": float('nan'), "accuracy": float('inf'), "lr": -float('inf')})

        # Should not crash and should be logged
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))
        assert len(log_files) == 1

        mtx.finish()


class TestExperimentContext:

    def test_context_manager(self, temp_logdir):
        """Test experiment context manager"""
        with mtx.ExperimentContext(temp_logdir) as exp:
            assert core._current_experiment is not None
            mtx.log({"test": 1})

        # Should be automatically finalized
        assert core._current_experiment is None

        # Check finalization was logged
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        log_files = list(experiments_dir.glob('*.jsonl'))

        with open(log_files[0], 'r') as f:
            lines = f.readlines()

        final_entry = json.loads(lines[-1])
        assert final_entry['type'] == 'metadata'
        assert final_entry['status'] == ExperimentStatus.COMPLETED.value


class TestSafeExecution:

    def test_safe_execute_success(self):
        """Test safe execute with successful function"""
        def test_func(a, b):
            return a + b

        result = core._safe_execute(test_func, 2, 3)
        assert result == 5

    def test_safe_execute_failure(self):
        """Test safe execute with failing function"""
        def failing_func():
            raise ValueError("Test error")

        # Should not raise exception, should return None
        result = core._safe_execute(failing_func)
        assert result is None


class TestRecovery:

    def test_incomplete_experiment_recovery(self, temp_logdir):
        """Test recovery of incomplete experiments"""
        # Create an incomplete experiment manually
        experiments_dir = Path(temp_logdir) / EXPERIMENTS_DIR
        experiments_dir.mkdir(parents=True, exist_ok=True)

        incomplete_file = experiments_dir / 'incomplete_experiment.jsonl'
        with open(incomplete_file, 'w') as f:
            metadata = {
                "type": "metadata",
                "experiment_id": "incomplete_experiment",
                "status": "running"
            }
            log_entry = {
                "type": "log",
                "data": {"step": 0, "loss": 1.0}
            }
            f.write(json.dumps(metadata) + '\n')
            f.write(json.dumps(log_entry) + '\n')

        # Init should trigger recovery
        mtx.init(temp_logdir)

        # Check that recovery was performed
        with open(incomplete_file, 'r') as f:
            lines = f.readlines()

        # Should have recovery metadata at end
        recovery_entry = json.loads(lines[-1])
        assert recovery_entry['type'] == 'metadata'
        assert recovery_entry['status'] == 'recovered'

        mtx.finish()


class TestEnums:

    def test_experiment_status_enum(self):
        """Test ExperimentStatus enum"""
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.INTERRUPTED.value == "interrupted"

        assert str(ExperimentStatus.RUNNING) == "running"


class TestErrorHandling:

    def test_log_without_init(self):
        """Test logging without initialization gives warning"""
        # Ensure no current experiment
        # Reset global state
        core._current_experiment = None

        with pytest.warns(UserWarning):
            mtx.log({"test": 1})

    def test_log_images_without_init(self, sample_image):
        """Test image logging without initialization gives warning"""
        # Ensure no current experiment
        # Reset global state
        core._current_experiment = None

        with pytest.warns(UserWarning):
            mtx.log_images(sample_image)

        plt.close(sample_image)

    def test_finish_without_init(self):
        """Test finish without initialization works gracefully"""
        # Ensure no current experiment
        # Reset global state
        core._current_experiment = None

        # Should not raise or warn - just do nothing
        mtx.finish()  # Should work without error
