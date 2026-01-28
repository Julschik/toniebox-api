"""Live connectivity test for the Tonie Cloud API.

This test requires valid credentials in .env and makes real API calls.
Skip in CI/CD environments where credentials are not available.
"""

import os

import pytest
from dotenv import load_dotenv

from tonie_api import TonieCloudSession


@pytest.fixture(scope="module")
def credentials() -> tuple[str, str]:
    """Load credentials from .env file."""
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    if not username or not password:
        pytest.skip("USERNAME and PASSWORD must be set in .env")
    return username, password


def test_api_reachable(credentials: tuple[str, str]) -> None:
    """Test that we can authenticate and reach the /me endpoint."""
    username, password = credentials
    session = TonieCloudSession(username, password)

    response = session.get(f"{TonieCloudSession.BASE_URL}/me")
    response.raise_for_status()

    data = response.json()
    assert "uuid" in data
    assert "email" in data
