"""Tests for the data repository."""

from __future__ import annotations

from spherexportal.repositories.mockdata import MockDataRepository
from spherexportal.repositories.projects import ProjectRepository


def test_loading_mock_data() -> None:
    project_repo = ProjectRepository()
    mock_repo = MockDataRepository.load_builtin_data()
    mock_repo.bootstrap_project_repository(project_repo)
