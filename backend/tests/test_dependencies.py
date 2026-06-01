def test_required_async_database_dependency_is_installed() -> None:
    import cryptography
    import greenlet

    assert cryptography is not None
    assert greenlet is not None
