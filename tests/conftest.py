import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def discover_fixtures(endpoint_dir):
    """Discover all response fixture files in an endpoint directory.

    Finds files matching *_response_*.txt sorted by name, so tests
    automatically run against every captured response.
    """
    path = FIXTURE_DIR / endpoint_dir
    if not path.exists():
        return []
    return sorted(path.glob("*_response_*.txt"))


def fixture_id(path):
    """Generate a readable test ID from a fixture path (e.g. 'css610_response_1')."""
    return path.stem


@pytest.fixture
def fixture_dir():
    """Return the path to the test fixtures directory."""
    return FIXTURE_DIR


def pytest_generate_tests(metafunc):
    """Auto-parametrize fixtures based on discovered response files."""
    if "link_response" in metafunc.fixturenames:
        files = discover_fixtures("link_b")
        metafunc.parametrize(
            "link_response",
            [f.read_text() for f in files],
            ids=[fixture_id(f) for f in files],
            indirect=False,
        )
    if "sys_response" in metafunc.fixturenames:
        files = discover_fixtures("sys_b")
        metafunc.parametrize(
            "sys_response",
            [f.read_text() for f in files],
            ids=[fixture_id(f) for f in files],
            indirect=False,
        )
