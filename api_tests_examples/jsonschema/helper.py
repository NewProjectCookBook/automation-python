import json
import allure
from jsonschema import RefResolver
from jsonschema.validators import validator_for
from typing import Any, Union


class SchemaConstruct:

    def __init__(self, *args: dict[str, Any]) -> None:
        self.schemas = [i for i in args if i]

    def _construct(self) -> RefResolver:
        """Schema construction"""
        schema_store = {}
        for index, schema in enumerate(self.schemas):
            schema_store.update({schema.get('$id', f'definitions-{index}.schema.json'): schema})
        return RefResolver.from_schema(schema=self.schemas[0], store=schema_store)

    def validation(self, response: Union[dict, bytes, str, bytearray]) -> None:
        with allure.step("json schema validation"):
            validator = validator_for(schema=True)
            validator = validator(schema=True, resolver=self._construct())
            if isinstance(response, (bytes, str, bytearray)):
                response = json.loads(response)
            validator.validate(response, self.schemas[0])
