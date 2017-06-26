import pytest


@pytest.fixture(scope='session')
def existing_patient_emr_cases(med_api, logged_in_pacient, logger):
    r = med_api.get('patient/emr/case')
    r.raise_for_status()
    cache = r.json()
    logger.info("{} emr_cases exist before the test: {!r}".format(cache['data'], cache['data']))
    if cache['data'] is None:
        return tuple()
    else:
        return tuple(_s['code'] for _s in cache['data'])


@pytest.yield_fixture(scope='function')
def cleanup_test_emr_cases(med_api, existing_patient_emr_cases, logged_in_pacient, logger):
    '''Use this fixture to clean up all test emr_cases at teardown.
    '''
    yield
    r = med_api.get('patient/emr/case')
    r.raise_for_status()
    results = r.json()['data']
    if results:
        logger.info("Cleaning up test emr_cases...")
        new_ids = set(_s['code'] for _s in results).difference(existing_patient_emr_cases)
        for _id in new_ids:
            r_del = med_api.delete('patient/emr/case', json={'id': _id})
            assert r_del.status_code == 200
    else:
        logger.warning("No emr_cases! Nothing to clean up.")


@pytest.fixture
def emr_cases(med_api, logged_in_pacient, cleanup_test_emr_cases):
    """
    This fixture ensures that predefined emr_cases for test are present.
    Returns a list of emr_cases items like: {"id": ..., "queries": ..., "documents", ...}
    """
    test_emr_cases = ('test_case_one', 'test_case_two', 'test_case_three')
    _list = list()
    for e_title in test_emr_cases:
        r = med_api.post('patient/emr/case', json={'title': e_title})
        assert r.status_code == 200
        _list.append({'id': r.json()['data']['id'], 'title': e_title})
    return tuple(_list)


def test_emr_cases_list(med_api, logged_in_pacient, emr_cases, logger):
    """
    Получение списка случаев ЭМК.
    """
    with pytest.allure.step("Get a list of all emr_cases"):
        logger.info("These emr_cases were added at setup: {!r}".
                    format(emr_cases))
        r = med_api.get('patient/emr/case')
        r.raise_for_status()

    with pytest.allure.step("Make sure it includes all emr_cases added before"):
        results = r.json()['data']
        results_list = [{'id': _r['code'], 'title': _r['display']} for _r in results]
        logger.info("All current emr_cases: {!r}".format(results_list))
        for _s in emr_cases:
            assert _s in results_list


POST_CASES = (
    dict(description="Adding emr_case with empty title",
         ok=False,
         post_data={"title": ""},
         expected_code=401),
    dict(description="Adding normal emr_case",
         ok=True,
         post_data={"title": "test_case_four"},
         expected_code=200),
    dict(description="Adding existing emr_case",
         ok=False,
         post_data={"title": "test_case_one"},
         expected_code=610),
    dict(description="Adding emr_case with empty request's body",
         ok=False,
         post_data={},
         expected_code=401)
)


@pytest.mark.parametrize('case', POST_CASES, ids=tuple(str(_c['post_data']) for _c in POST_CASES))
def test_emr_case_post(case, med_api, logged_in_pacient, emr_cases, logger, cleanup_test_emr_cases):
    """
    Добавление нового случая ЭМК для пользователя.
    """
    with pytest.allure.step(case['description']):
        r_post = med_api.post('patient/emr/case', json=case['post_data'])
        logger.info("Response: {!r}".format(r_post.content))

    with pytest.allure.step("Verifying response (expecting ok = {})".format(case['ok'])):
        assert r_post.ok == case['ok']
        assert r_post.json()['code'] == case['expected_code']  # created
        if case['ok']:
            with pytest.allure.step("Make sure that emr_case was added"):
                new_emr_case = case['post_data']
                new_emr_case['id'] = r_post.json()['data']['id']
                r = med_api.get('patient/emr/case')
                results = r.json()['data']
                results_list = [{'id': _r['code'], 'title': _r['display']} for _r in results]
                assert new_emr_case in results_list


def test_emr_case_put(emr_cases, med_api, logged_in_pacient, logger, cleanup_test_emr_cases):
    """
    Изменяем параметры случая ЭМК для пользователя.
    """
    with pytest.allure.step('Change emr_case title'):
        r_put = med_api.put('patient/emr/case', json={'id': emr_cases[0]['id'],
                                                    'title': emr_cases[0]['title'] + '_new'}
                            )
        logger.info("Response: {!r}".format(r_put.content))
        r_put.raise_for_status()
        r = med_api.get('patient/emr/case')
        results = r.json()['data']
        assert {'code': emr_cases[0]['id'],
                'display': emr_cases[0]['title'] + '_new'} in results
    with pytest.allure.step('Change title to existing title'):
        r_put = med_api.put('patient/emr/case', json={'id': emr_cases[0]['id'],
                                                      'title': emr_cases[1]['title']
                                                      })
        logger.info("Response: {!r}".format(r_put.content))
        assert not r_put.ok
