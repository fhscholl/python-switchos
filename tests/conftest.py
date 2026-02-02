import ast
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def discover_fixtures(endpoint_dir):
    """Discover response/expected fixture pairs in an endpoint directory.

    Finds files matching *_response_*.txt and pairs each with its
    .expected file (Python dict literal). Returns list of
    (response_text, expected_dict, fixture_id) tuples.
    """
    path = FIXTURE_DIR / endpoint_dir
    if not path.exists():
        return []
    pairs = []
    for response_file in sorted(path.glob("*_response_*.txt")):
        expected_file = response_file.with_suffix(".expected")
        response_text = response_file.read_text()
        expected_dict = None
        if expected_file.exists():
            expected_dict = ast.literal_eval(expected_file.read_text())
        pairs.append((response_text, expected_dict, response_file.stem))
    return pairs


@pytest.fixture
def fixture_dir():
    """Return the path to the test fixtures directory."""
    return FIXTURE_DIR


def pytest_generate_tests(metafunc):
    """Auto-parametrize fixtures based on discovered response files."""
    if "link_response" in metafunc.fixturenames or "link_expected" in metafunc.fixturenames:
        pairs = discover_fixtures("link_b")
        if "link_response" in metafunc.fixturenames and "link_expected" in metafunc.fixturenames:
            metafunc.parametrize(
                "link_response,link_expected",
                [(r, e) for r, e, _ in pairs],
                ids=[fid for _, _, fid in pairs],
                indirect=False,
            )
        elif "link_response" in metafunc.fixturenames:
            metafunc.parametrize(
                "link_response",
                [r for r, _, _ in pairs],
                ids=[fid for _, _, fid in pairs],
                indirect=False,
            )
    if "sys_response" in metafunc.fixturenames or "sys_expected" in metafunc.fixturenames:
        pairs = discover_fixtures("sys_b")
        if "sys_response" in metafunc.fixturenames and "sys_expected" in metafunc.fixturenames:
            metafunc.parametrize(
                "sys_response,sys_expected",
                [(r, e) for r, e, _ in pairs],
                ids=[fid for _, _, fid in pairs],
                indirect=False,
            )
        elif "sys_response" in metafunc.fixturenames:
            metafunc.parametrize(
                "sys_response",
                [r for r, _, _ in pairs],
                ids=[fid for _, _, fid in pairs],
                indirect=False,
            )
