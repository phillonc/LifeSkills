"""Tests for the DSDM technique tools."""

import pytest

from agents_framework.tools import (
    BusinessCaseTool,
    MoSCoWPrioritisationTool,
    RequirementsAnalysisTool,
    RiskLogTool,
    TimeboxPlannerTool,
)


def _prl(items):
    return RequirementsAnalysisTool().run(items=items)["prl"]


# -- RequirementsAnalysisTool ---------------------------------------------
def test_requirements_normalises_strings_and_aliases():
    prl = _prl(["A plain requirement", {"title": "Login", "priority": "Must", "effort": 3}])
    assert prl[0]["priority"] == "S"          # default
    assert prl[0]["id"] == "R001"
    assert prl[1]["priority"] == "M"          # "Must" -> "M"
    assert prl[1]["effort"] == 3.0


def test_requirements_rejects_bad_priority():
    with pytest.raises(ValueError):
        RequirementsAnalysisTool().run(items=[{"title": "x", "priority": "urgent"}])


def test_requirements_rejects_empty_title():
    with pytest.raises(ValueError):
        RequirementsAnalysisTool().run(items=[{"title": "  "}])


# -- MoSCoWPrioritisationTool ---------------------------------------------
def test_moscow_extracts_mus_and_flags_imbalance():
    prl = _prl(
        [
            {"title": "m1", "priority": "M", "effort": 7},
            {"title": "m2", "priority": "M", "effort": 1},
            {"title": "s1", "priority": "S", "effort": 1},
            {"title": "c1", "priority": "C", "effort": 1},
        ]
    )
    out = MoSCoWPrioritisationTool().run(prl=prl)
    assert {r["title"] for r in out["minimum_usable_subset"]} == {"m1", "m2"}
    assert out["must_have_pct"] == 80.0       # 8 / 10
    assert out["balanced"] is False
    assert out["warnings"]


def test_moscow_balanced_passes():
    prl = _prl(
        [
            {"title": "m", "priority": "M", "effort": 6},
            {"title": "s", "priority": "S", "effort": 2},
            {"title": "c", "priority": "C", "effort": 2},
        ]
    )
    out = MoSCoWPrioritisationTool().run(prl=prl)
    assert out["must_have_pct"] == 60.0
    assert out["balanced"] is True


# -- TimeboxPlannerTool ----------------------------------------------------
def test_timebox_includes_musts_defers_low_priority():
    prl = _prl(
        [
            {"title": "must", "priority": "M", "effort": 5},
            {"title": "should", "priority": "S", "effort": 4},
            {"title": "could", "priority": "C", "effort": 4},
            {"title": "wont", "priority": "W", "effort": 1},
        ]
    )
    out = TimeboxPlannerTool().run(prl=prl, capacity=10)
    titles = {r["title"] for r in out["included"]}
    assert "must" in titles and "should" in titles
    assert {r["title"] for r in out["deferred"]} == {"could"}  # 5+4+4 > 10
    assert all(r["title"] != "wont" for r in out["included"])  # Won't excluded
    assert out["committed_effort"] == 9


def test_timebox_flags_overcommitted_musts():
    prl = _prl([{"title": "big", "priority": "M", "effort": 20}])
    out = TimeboxPlannerTool().run(prl=prl, capacity=10)
    assert out["included"][0]["title"] == "big"   # musts always committed
    assert out["warnings"]


# -- BusinessCaseTool ------------------------------------------------------
def test_business_case_computes_roi_and_payback():
    out = BusinessCaseTool().run(costs=[40_000, 10_000], benefits=[100_000], period_years=2)
    assert out["total_cost"] == 50_000
    assert out["net_benefit"] == 50_000
    assert out["roi_pct"] == 100.0
    assert out["viable"] is True
    assert out["payback_years"] == 1.0           # 50k / (100k/2)


# -- RiskLogTool -----------------------------------------------------------
def test_risk_log_ranks_by_exposure():
    out = RiskLogTool().run(
        risks=[
            {"description": "low", "probability": 0.1, "impact": 2},
            {"description": "high", "probability": 0.9, "impact": 9},
        ]
    )
    assert out["top_risk"]["description"] == "high"
    assert out["risks"][0]["exposure"] == 8.1


def test_risk_log_rejects_bad_probability():
    with pytest.raises(ValueError):
        RiskLogTool().run(risks=[{"description": "x", "probability": 2, "impact": 1}])
