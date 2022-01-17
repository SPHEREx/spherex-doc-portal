"""The repository holds the documentation metadata."""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import AnyHttpUrl, BaseModel, Field


class SsdcMsModel(BaseModel):
    """Model for ssdc-ms document metadata."""

    handle: str

    title: str

    url: AnyHttpUrl


class DatasetModel(BaseModel):
    """Model for the dataset file."""

    ssdc_ms: List[SsdcMsModel] = Field(..., alias="ssdc-ms")

    @classmethod
    def from_yaml(cls, path: Path) -> DatasetModel:
        data = yaml.safe_load(path.read_text())
        return cls.parse_obj(data)
