import pytest
import json
from extra import utils


@pytest.fixture(scope='module')
def json_schema():
    with open('api/json/0.1/schemas/practitioner.json') as f_schema:
        schema = json.load(f_schema)
        return schema

def test_get_practitioner_profile(med_api, logged_in_practitioner, json_schema):
    '''Получение информации об авторизованном докторе через API (/practitioner/profile).
    '''
    with pytest.allure.step("Sending user profile request: expecting ok response"):
        r = med_api.get('practitioner/profile')
        r.raise_for_status()
        utils.validate_json(r.json()['data'], json_schema['profile']['get']['out']['properties'])
