PLAIN_API_KEY_PREFIX = "plain:"
ENCRYPTED_API_KEY_PREFIX = "enc:v1:"


def store_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    cleaned_key = api_key.strip()
    if not cleaned_key:
        return None
    return f"{PLAIN_API_KEY_PREFIX}{cleaned_key}"


def load_api_key(stored_value: str | None) -> str:
    if not stored_value:
        return ""
    if stored_value.startswith(PLAIN_API_KEY_PREFIX):
        return stored_value.removeprefix(PLAIN_API_KEY_PREFIX)
    if stored_value.startswith(ENCRYPTED_API_KEY_PREFIX):
        raise ValueError("当前版本暂不支持读取加密密钥，请重新保存 API Key")
    return stored_value


def has_stored_api_key(stored_value: str | None) -> bool:
    return bool(stored_value)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


def mask_stored_api_key(stored_value: str | None) -> str:
    if not stored_value:
        return ""
    if stored_value.startswith(ENCRYPTED_API_KEY_PREFIX):
        return "enc:v1:****"
    return mask_api_key(load_api_key(stored_value))
