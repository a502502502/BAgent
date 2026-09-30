import pytest

from harness.contracts import CATALOG


@pytest.mark.parametrize("contract", CATALOG, ids=lambda contract: contract.rule_id)
def test_rule_has_a_block_and_an_admission(contract):
    ok, detail = contract.check()
    assert ok, detail
