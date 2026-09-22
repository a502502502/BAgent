"""TENNIS BAN 22/09/2026 — test disabilitato."""
import pytest

pytestmark = pytest.mark.skip(reason="TENNIS BAN 22/09/2026")


def test_tennis_module_disabled():
    assert False, "unreachable"
