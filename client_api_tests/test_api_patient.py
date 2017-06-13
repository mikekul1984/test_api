import pytest
import json
from extra import utils


@pytest.fixture(scope='module')
def json_schema():
    with open('api/json/0.1/schemas/patient.json') as f_schema:
        schema = json.load(f_schema)
        return schema

def test_get_patient_profile(med_api, logged_in_pacient, json_schema):
    '''Получение информации об авторизованном пользователе через API (/patient/profile).
    '''
    with pytest.allure.step("Sending user profile request: expecting ok response"):
        r = med_api.get('patient/profile')
        r.raise_for_status()
        utils.validate_json(r.json()['data'], json_schema['profile']['get']['out']['properties'])

def test_get_patient_emr(med_api, logged_in_pacient, json_schema):
    '''Получение информации об авторизованном пользователе через API (/patient/emr).
    '''
    with pytest.allure.step("Sending user emr request: expecting ok response"):
        r = med_api.get('patient/emr')
        r.raise_for_status()
        utils.validate_json(r.json()['data'], json_schema['emr']['get']['out']['properties'])
