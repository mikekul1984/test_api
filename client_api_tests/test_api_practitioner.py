import pytest
import json
from extra import utils


@pytest.fixture(scope='module')
def json_schema():
    with open('api/json/{}/schemas/practitioner.json'.
                      format(pytest.config.getoption("--api_version"))) \
            as f_schema:
        schema = json.load(f_schema)
        return schema


def test_get_practitioner_profile(med_api, logged_in_practitioner, json_schema):
    '''Получение информации об авторизованном докторе через API (/practitioner/profile).
    '''
    with pytest.allure.step("Sending user profile request: expecting ok response"):
        r = med_api.get('practitioner/profile')
        r.raise_for_status()
        utils.validate_json(r.json()['data'], json_schema['profile']['get']['out']['properties'])


def test_get_practitioner_patient(med_api, logged_in_practitioner, json_schema):
    '''Получение информации об пациентах доктора через API (/practitioner/patient).
    '''
    with pytest.allure.step("Sending user profile request: expecting ok response"):
        r = med_api.get('practitioner/patient')
        r.raise_for_status()
        practitioner_patient_schema = json_schema['patient']['get']['out']['items']['properties']
        practitioner_patient_schema.pop('id')
        if r.json():
            for _p in r.json()['data']:
                utils.validate_json(_p, practitioner_patient_schema)
