import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir():
    """Return the path to the test fixtures directory."""
    return FIXTURE_DIR


@pytest.fixture
def link_response():
    """Load the raw CSS610 link.b response fixture."""
    return (FIXTURE_DIR / "link_b" / "css610_response.txt").read_text()


@pytest.fixture
def sys_response():
    """Load the raw CSS610 sys.b response fixture."""
    return (FIXTURE_DIR / "sys_b" / "css610_response.txt").read_text()
