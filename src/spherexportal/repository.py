"""The repository holds the documentation metadata."""

from __future__ import annotations

from operator import attrgetter
from pathlib import Path
from typing import List

import yaml
from pydantic import AnyHttpUrl, BaseModel, Field

from spherexportal.config import config


class Document(BaseModel):
    """Model for ssdc-ms document metadata."""

    handle: str

    title: str

    url: AnyHttpUrl


class DatasetModel(BaseModel):
    """Model for the dataset file."""

    ssdc_ms: List[Document] = Field(alias="ssdc-ms", default_factory=list)
    ssdc_pm: List[Document] = Field(alias="ssdc-pm", default_factory=list)
    ssdc_tr: List[Document] = Field(alias="ssdc-tr", default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> DatasetModel:
        data = yaml.safe_load(path.read_text())
        return cls.parse_obj(data)


class DocumentRepository:
    """A repository for access document metadata."""

    def __init__(self, parsed_dataset: DatasetModel) -> None:
        self._data = parsed_dataset

    def get_ms_by_handle(self, ascending: bool = True) -> List[Document]:
        return sorted(
            self._data.ssdc_ms, key=attrgetter("handle"), reverse=not ascending
        )

    def get_pm_by_handle(self, ascending: bool = True) -> List[Document]:
        return sorted(
            self._data.ssdc_pm, key=attrgetter("handle"), reverse=not ascending
        )

    def get_tr_by_handle(self, ascending: bool = True) -> List[Document]:
        return sorted(
            self._data.ssdc_tr, key=attrgetter("handle"), reverse=not ascending
        )


class RepositoryDependency:
    def __init__(self) -> None:
        dataset = DatasetModel.from_yaml(config.dataset_path)
        self._repo = DocumentRepository(dataset)

    async def __call__(self) -> DocumentRepository:
        return self._repo


repository_dependency = RepositoryDependency()
