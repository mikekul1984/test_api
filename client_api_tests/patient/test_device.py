import pytest


@pytest.fixture(scope='session')
def existing_patient_devices(med_api, logged_in_pacient, logger):
    r = med_api.get('patient/device')
    r.raise_for_status()
    cache = r.json()
    logger.info("{} devices exist before the test: {!r}".format(cache['data'], cache['data']))
    if cache['data'] is None:
        return tuple()
    else:
        return tuple(_s['id'] for _s in cache['data'])


@pytest.yield_fixture(scope='function')
def cleanup_test_devices(med_api, existing_patient_devices, logged_in_pacient, logger):
    '''Use this fixture to clean up all test devices at teardown.
    '''
    yield
    r = med_api.get('patient/device')
    r.raise_for_status()
    results = r.json()['data']
    if results:
        logger.info("Cleaning up test devices...")
        new_ids = set(_s['id'] for _s in results).difference(existing_patient_devices)
        for _id in new_ids:
            r_del = med_api.delete('patient/device', json={'id': _id})
            assert r_del.status_code == 200
    else:
        logger.warning("No devices! Nothing to clean up.")


@pytest.fixture
def devices(med_api, logged_in_pacient, cleanup_test_devices):
    """
    This fixture ensures that predefined devices for test are present.
    Returns a list of devices items like: {"id": ..., "queries": ..., "documents", ...}
    """
    test_devices = (  # order is very important (tests rely on it)
        ('42', 'tonometer'),
        ('4242', 'cardiograph'),
        ('24', 'vitaphone')
    )
    _list = list()
    for d_udn, d_type in test_devices:
        r = med_api.post('patient/device', json={'udn': d_udn, 'device_type': d_type})
        assert r.status_code == 200
        _list.append({'id': r.json()['data']['id'], 'udn': d_udn, 'device_type': d_type})
    return tuple(_list)


def test_devices_list(med_api, logged_in_pacient, devices, logger):
    """
    Получение списка устройств.
    """
    with pytest.allure.step("Get a list of all devices"):
        logger.info("These devices were added at setup: {!r}".
                    format(devices))
        r = med_api.get('patient/device')
        r.raise_for_status()

    with pytest.allure.step("Make sure it includes all devices added before"):
        results = r.json()['data']
        results_list = [{'id': _r['id'], 'device_type': _r['device_type'], 'udn': _r['udn']} for _r in results]
        logger.info("All current devices: {!r}".format(results_list))
        for _s in devices:
            assert _s in results_list
