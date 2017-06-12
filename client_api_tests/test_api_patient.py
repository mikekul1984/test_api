import pytest


def test_login_positive(med_api, logged_in_user):
    '''Получение информации об авторизованном пользователе через API (/me).
    '''
    with pytest.allure.step("Sending user profile request: expecting ok response"):
        r = med_api.get('patient/profile')
        r.raise_for_status()