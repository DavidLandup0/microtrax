"""
Tests for microtrax enums
"""
from microtrax.enums import ExperimentStatus


class TestExperimentStatus:

    def test_enum_values(self):
        """Test enum values are correct"""
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.INTERRUPTED.value == "interrupted"

    def test_enum_string_representation(self):
        """Test string representation of enum"""
        assert str(ExperimentStatus.RUNNING) == "running"
        assert str(ExperimentStatus.COMPLETED) == "completed"
        assert str(ExperimentStatus.INTERRUPTED) == "interrupted"

    def test_enum_comparison(self):
        """Test enum comparison"""
        assert ExperimentStatus.RUNNING == ExperimentStatus.RUNNING
        assert ExperimentStatus.RUNNING != ExperimentStatus.COMPLETED

    def test_enum_in_list(self):
        """Test enum membership in lists"""
        valid_statuses = [ExperimentStatus.COMPLETED.value, ExperimentStatus.INTERRUPTED.value]

        assert ExperimentStatus.COMPLETED.value in valid_statuses
        assert ExperimentStatus.INTERRUPTED.value in valid_statuses
        assert ExperimentStatus.RUNNING.value not in valid_statuses
