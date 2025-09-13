import utils


def test_is_all_nines_api_key_true_cases():
    assert utils.is_all_nines_api_key("999999")
    assert utils.is_all_nines_api_key("sk-ant-999")


def test_is_all_nines_api_key_false_cases():
    assert not utils.is_all_nines_api_key("123456")
    assert not utils.is_all_nines_api_key("sk-ant-123")
    assert not utils.is_all_nines_api_key(None)
