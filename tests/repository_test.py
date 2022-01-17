"""Tests for the data repository."""

from __future__ import annotations

from pathlib import Path

import pytest

from spherexportal.repository import DatasetModel, DocumentRepository


@pytest.fixture
def dataset() -> DatasetModel:
    path = Path(__file__).parent / "dataset.example.yaml"
    parsed_dataset = DatasetModel.from_yaml(path)
    return parsed_dataset


def tests_datasetmodel(dataset: DatasetModel) -> None:
    assert len(dataset.ssdc_ms) == 2


def test_repository(dataset: DatasetModel) -> None:
    repo = DocumentRepository(dataset)
    ssdc_ms_docs = repo.get_ms_by_handle()
    assert ssdc_ms_docs[0].handle == "SSDC-MS-001"
    assert ssdc_ms_docs[1].handle == "SSDC-MS-002"

    ssdc_ms_docs_rev = repo.get_ms_by_handle(ascending=False)
    assert ssdc_ms_docs_rev[0].handle == "SSDC-MS-002"
    assert ssdc_ms_docs_rev[1].handle == "SSDC-MS-001"
