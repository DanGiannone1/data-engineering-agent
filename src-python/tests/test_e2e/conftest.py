import pytest

BASE_URL = "http://localhost:7071"


def pytest_addoption(parser):
    parser.addoption("--base-url", default=BASE_URL)


@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url").rstrip("/")
