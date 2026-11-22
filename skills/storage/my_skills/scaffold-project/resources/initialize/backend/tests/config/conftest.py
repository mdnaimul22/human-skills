import pytest


@pytest.fixture(autouse=True)
def setup_test_database():
    """Bypass global DB fixture for pure configuration unit tests."""
    yield
