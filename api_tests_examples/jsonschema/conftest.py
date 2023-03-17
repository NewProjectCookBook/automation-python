# System
import json
import os
import pytest
from _pytest.fixtures import SubRequest

from http import HTTPStatus

from typing import Any


@pytest.fixture(scope='module')
def get_base_schema(status_code: HTTPStatus, get_project_root: str) -> dict[str, Any]:
    """Базовая схема данных для списка элементов в поле data"""
    with open(os.path.join(get_project_root, os.path.dirname(__file__), 'base.schema.json'), 'rb') as f:
        return json.load(f).get(str(status_code))


@pytest.fixture(scope='module')
def get_definitions_schema(request: SubRequest, status_code: HTTPStatus) -> dict[str, Any]:
    """Фикстура, которая возвращает схему данных"""
    with open(os.path.join(request.fspath.dirname, "test_/definitions.schema.json"), 'rb') as f:
        return json.load(f).get(str(status_code))
