import json
from datetime import date

import pytest

from kiwi_ask.m0_tools import check_rent_increase, run_tool_call


@pytest.mark.parametrize(
    (
        "last_increase",
        "notice_date",
        "effective_date",
        "allowed",
        "notice_ok",
        "earliest",
    ),
    [
        ("2025-04-30", "2025-10-01", "2025-12-30", False, True, "2026-04-30"),
        ("2025-04-30", "2026-02-28", "2026-04-30", True, True, "2026-04-30"),
        ("2025-04-30", "2026-03-02", "2026-04-30", False, False, "2026-05-01"),
        ("2025-04-30", "2026-03-01", "2026-04-30", True, True, "2026-04-30"),
        ("2024-02-29", "2024-12-30", "2025-02-28", True, True, "2025-02-28"),
    ],
    ids=["eight-months", "twelve-months", "59-days", "60-days", "leap-day"],
)
def test_check_rent_increase(
    last_increase: str,
    notice_date: str,
    effective_date: str,
    allowed: bool,
    notice_ok: bool,
    earliest: str,
) -> None:
    result = check_rent_increase(
        date.fromisoformat(last_increase),
        date.fromisoformat(notice_date),
        date.fromisoformat(effective_date),
    )

    assert result["allowed"] is allowed
    assert result["notice_period_ok"] is notice_ok
    assert result["earliest_effective_date"] == earliest
    assert result["reason"]


def test_check_rent_increase_without_effective_date() -> None:
    result = check_rent_increase(
        last_increase=date(2025, 4, 30),
        notice_date=date(2025, 12, 30),
    )

    assert result["earliest_effective_date"] == "2026-04-30"
    assert result["allowed"] is None
    assert result["notice_period_ok"] is None
    assert "未提供拟生效日" in result["reason"]


def test_run_tool_call_reports_invalid_date() -> None:
    payload = json.loads(
        run_tool_call(
            "check_rent_increase",
            '{"last_increase":"2025-04-30","notice_date":"bad-date"}',
        )
    )

    assert payload["error"] == "Invalid tool arguments."
    assert payload["details"][0]["loc"] == ["notice_date"]
    assert "input" not in payload["details"][0]


def test_run_tool_call_rejects_unknown_tool() -> None:
    payload = json.loads(run_tool_call("unexpected_tool", "{}"))

    assert payload == {"error": "Unknown tool name."}
