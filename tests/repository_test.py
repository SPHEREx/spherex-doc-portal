"""Tests for the data repository."""

from __future__ import annotations

from pathlib import Path

import pytest

from spherexportal.repository import DatasetModel


@pytest.fixture
def dataset() -> DatasetModel:
    path = Path(__file__).parent / "dataset.example.yaml"
    parsed_dataset = DatasetModel.from_yaml(path)
    return parsed_dataset


def tests_datasetmodel(dataset: DatasetModel) -> None:
    assert len(dataset.ssdc_ms) == 2
