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


POST_CASES = (
    dict(description="Adding device with empty udn",
         ok=False,
         post_data={"udn": "", "device_type": "tonometer"},
         expected_code=502),
    dict(description="Adding normal device",
         ok=True,
         post_data={"udn": "some_device", "device_type": "alivecor"},
         expected_code=200),
    dict(description="Adding device with empty device_type",
         ok=False,
         post_data={"udn": "some_device", "device_type": ""},
         expected_code=401),
    dict(description="Adding device with empty request's body",
         ok=False,
         post_data={},
         expected_code=401)
)


@pytest.mark.parametrize('case', POST_CASES, ids=tuple(str(_c['post_data']) for _c in POST_CASES))
def test_device_post(case, med_api, logged_in_pacient, logger, cleanup_test_devices):
    """
    Добавление нового устройства для пользователя.
    """
    with pytest.allure.step(case['description']):
        r_post = med_api.post('patient/device', json=case['post_data'])
        logger.info("Response: {!r}".format(r_post.content))

    with pytest.allure.step("Verifying response (expecting ok = {})".format(case['ok'])):
        assert r_post.ok == case['ok']
        assert r_post.json()['code'] == case['expected_code']  # created
        if case['ok']:
            with pytest.allure.step("Make sure that device was added"):
                new_device = case['post_data']
                new_device['id'] = r_post.json()['data']['id']
                r = med_api.get('patient/device')
                results = r.json()['data']
                results_list = [{'id': _r['id'], 'device_type': _r['device_type'], 'udn': _r['udn']} for _r in results]
                assert new_device in results_list


def test_device_put(devices, med_api, logged_in_pacient, logger, cleanup_test_devices):
    """
    Изменяем параметры устройства для пользователя.
    """
    with pytest.allure.step('Change device udn'):
        r_put = med_api.put('patient/device', json={'id': devices[0]['id'],
                                                    'udn': devices[0]['udn'] + '_new'}
                            )
        logger.info("Response: {!r}".format(r_put.content))
        r_put.raise_for_status()
        r = med_api.get('patient/device')
        results = r.json()['data']
        # results_list = [{'id': _r['id'], 'device_type': _r['device_type'], 'udn': _r['udn']} for _r in results]
        devices_status = {_r['id']: _r['active'] for _r in results}
        assert {'id': devices[0]['id'],
                'udn': devices[0]['udn'] + '_new',
                'device_type': devices[0]['device_type'],
                'active': devices_status[devices[0]['id']],
                'last_use': None} in results
    with pytest.allure.step('Change device active status'):
        r_put = med_api.put('patient/device', json={'id': devices[1]['id'],
                                                    'udn': devices[1]['udn'],
                                                    'active': not devices_status[devices[1]['id']]}
                            )
        logger.info("Response: {!r}".format(r_put.content))
        r_put.raise_for_status()
        r = med_api.get('patient/device')
        results = r.json()['data']
        assert {'id': devices[1]['id'],
                'udn': devices[1]['udn'],
                'device_type': devices[1]['device_type'],
                'active': not devices_status[devices[1]['id']],
                'last_use': None} in results
    with pytest.allure.step('Change to wrong attributes'):
        r_put = med_api.put('patient/device', json={'wrong_attr': 'wrong_value'})
        logger.info("Response: {!r}".format(r_put.content))
        assert not r_put.ok
