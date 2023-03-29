from http import HTTPStatus

import allure
import pytest

from clients.api_client import Headers
from api_tests_examples.jsonschema.helper import SchemaConstruct
from urls import UrlsAPI    # enum that contains some api urls


@pytest.mark.parametrize(
    'status_code, data',
    [pytest.param(HTTPStatus.OK, 1)] +
    [pytest.param(HTTPStatus.INTERNAL_SERVER_ERROR, 99999)] +
    [pytest.param(HTTPStatus.BAD_REQUEST, 'yasherka')],
    scope="module")
@pytest.mark.api_test
@allure.title('Checking of some API')
def test_api(get_base_schema, get_definitions_schema, get_api_client, status_code, data):
    response = get_api_client.get(path=UrlsAPI.url_get_applicant_model_versions.value.format(model_id=data),
                                  headers=Headers.JSON_TYPE, status_code=status_code)
    SchemaConstruct(get_base_schema, get_definitions_schema).validation(response=response.content)
