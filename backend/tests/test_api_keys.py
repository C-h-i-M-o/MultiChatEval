from app.core.api_keys import load_api_key, mask_stored_api_key, store_api_key


def test_plain_api_key_storage_round_trip() -> None:
    stored_key = store_api_key(" sk-test-1234 ")

    assert stored_key == "plain:sk-test-1234"
    assert load_api_key(stored_key) == "sk-test-1234"
    assert mask_stored_api_key(stored_key) == "sk-t****1234"


def test_mask_encrypted_key_placeholder() -> None:
    assert mask_stored_api_key("enc:v1:ciphertext") == "enc:v1:****"
