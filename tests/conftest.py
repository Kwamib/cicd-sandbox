import os

import pytest


def pytest_configure(config):
    if os.environ.get("CI") and not (os.environ.get("TEST_DATABASE_URL") and os.environ.get("REDIS_TEST_URL")):
        raise pytest.UsageError(
            "Running in CI without TEST_DATABASE_URL and REDIS_TEST_URL: "
            "the integration tests would skip, and the run would pass without testing them."
        )
