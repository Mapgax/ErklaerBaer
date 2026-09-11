from datetime import UTC, datetime

import pytest

from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.errors import BudgetExceeded


def test_budget_reservation_and_dry_run(tmp_path):
    ledger = BudgetLedger(tmp_path / "usage.json")
    assert ledger.reserve("llm_calls", 2, 3, dry_run=True) == 2
    assert ledger.current("llm_calls") == 0
    assert ledger.reserve("llm_calls", 2, 3, dry_run=False) == 2
    with pytest.raises(BudgetExceeded):
        ledger.reserve("llm_calls", 2, 3, dry_run=False)
    month = datetime.now(UTC).strftime("%Y-%m")
    assert month in ledger.load()["months"]
