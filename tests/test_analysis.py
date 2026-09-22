import importlib.util
import pytest


def test_inventory_value_and_annual_opportunity_cost():
    assert importlib.util.find_spec("analysis") is not None, "Analysis module not implemented"
    from analysis import value_inventory, opportunity_cost
    stock_value = value_inventory(mean_stock=100, unit_cost_ars=200, ars_per_usd=1000)
    assert stock_value == 20
    assert opportunity_cost(stock_value, annual_return=0.05) == 1
    assert opportunity_cost(stock_value, annual_return=-0.05) == -1
    with pytest.raises(ValueError):
        value_inventory(mean_stock=100, unit_cost_ars=200, ars_per_usd=0)


def test_original_workbook_cost_and_inventory_reconstruction():
    from pathlib import Path
    import analysis
    assert hasattr(analysis, "read_inventory"), "Workbook audit not implemented"
    result = analysis.read_inventory(Path(__file__).parents[1] / "data/raw/inventory.xlsx")
    assert result["pallet_bags"] == 1260
    assert result["pallet_cost_ars"] == 7574225
    assert result["unit_cost_ars"] == pytest.approx(7574225 / 1260)
    assert result["unit_cost_ars"] != 7900
    assert result["stock_count"] == 37
    assert result["stock_sum"] == 152163
    assert result["mean_stock"] == pytest.approx(152163 / 37)
    assert result["opening_stock"] == 3396
    assert result["purchases"] == 47880
    assert result["sales"] == 47528
    assert result["closing_stock"] == 3748
    audit = {row["source_row"]: row for row in result["stock_audit"]}
    assert 52 not in audit
    assert audit[34]["original_balance"] is None
    assert audit[34]["corrected_balance"] == 4956
    assert audit[35]["corrected_balance"] == 3443
    assert audit[51]["adjustment"] == 2520


def test_dated_market_evidence_and_full_precision_results():
    from pathlib import Path
    from decimal import Decimal
    import analysis
    assert hasattr(analysis, "analyze"), "Dated scenario pipeline not implemented"
    root = Path(__file__).parents[1]
    result = analysis.analyze(root)
    value = Decimal(152163) / 37 * Decimal(7574225) / 1260 / Decimal("1183.78")
    assert result["unit_cost_usd"] == pytest.approx(5.078046328320873)
    assert result["stock_value_usd"] == pytest.approx(float(value))
    assert result["exchange_rate"]["date"] == "2025-06-02"
    for fund, percent in zip(result["funds"], ["9.901322", "4.780024"], strict=True):
        assert fund["as_of_date"] == "2025-05-31"
        assert fund["return_type"] == "navSourced"
        assert fund["currency"] == "USD"
        assert fund["annual_cost_usd"] == pytest.approx(float(value * Decimal(percent) / 100))
    assert round(result["funds"][0]["annual_cost_usd"], 2) == 2067.75
    assert round(result["funds"][1]["annual_cost_usd"], 2) == 998.24


def test_mixed_return_dates_are_rejected():
    import analysis
    assert hasattr(analysis, "validate_funds"), "Comparable-period validation not implemented"
    funds = [{"currency": "USD", "as_of_date": date, "period": "1y", "return_type": "navSourced"}
             for date in ["2025-05-31", "2026-05-31"]]
    with pytest.raises(ValueError, match="comparable"):
        analysis.validate_funds(funds)
