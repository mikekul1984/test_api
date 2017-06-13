import pytest
import jsonschema


def validate_json(json_response, schema_json):
    """ Функция валидации json """

    with pytest.allure.step("Валидация json-ответа"):
        try:
            validator = jsonschema.Draft4Validator(schema_json)
            validator.validate(json_response, schema_json)
        except jsonschema.ValidationError as e:
            raise AssertionError(e)
