"""Fixtures for Session 07's in-memory fake (not database integration)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAKE_PATH = ROOT / "exercises/07-pytest-architecture/support/fake_pipeline.py"


@pytest.fixture(scope="session")
def pipeline_type() -> type[Any]:
    """Load the supplied fake once; the type itself holds no test data."""
    spec = importlib.util.spec_from_file_location("session07_fake_pipeline", FAKE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import FakePipeline from {FAKE_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses looks up the module by name
    spec.loader.exec_module(module)
    return module.FakePipeline


@pytest.fixture(scope="function")
def pipeline(pipeline_type: type[Any]) -> Iterator[Any]:
    """New processing state per test; cleanup also runs after a failed assertion."""
    instance = pipeline_type()
    try:
        yield instance
    finally:
        instance.reset()
