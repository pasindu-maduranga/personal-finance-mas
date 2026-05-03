"""
test_budget_checker.py
~~~~~~~~~~~~~~~~~~~~~~
Comprehensive test suite for the budget_checker tool (Budget Advisor Agent).

Covers:
    - Happy path (On Budget, Overspent, Within Budget)
    - Edge cases (missing categories, zero budget, floating point precision)
    - Negative / security tests (missing file, invalid JSON, non-numeric budgets, negative budgets)
"""

import json
import os
import tempfile

import pytest

from tools.budget_checker import check_budget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(data: dict | list | str, suffix=".json") -> str:
    """Write JSON data to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    if isinstance(data, str):
        tmp.write(data) # Write raw string for malformed JSON tests
    else:
        json.dump(data, tmp)
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestCheckBudgetHappyPath:

    def test_overspent_category(self):
        """Expense > Budget must return 'Overspent'."""
        budget_path = _write_json({"Food": 10000})
        try:
            result = check_budget({"Food": 12000}, budget_path)
            assert result["Food"]["status"] == "Overspent"
            assert result["Food"]["difference"] == -2000.0
        finally:
            os.unlink(budget_path)

    def test_within_budget_category(self):
        """Expense < Budget must return 'Within Budget'."""
        budget_path = _write_json({"Food": 10000})
        try:
            result = check_budget({"Food": 8000}, budget_path)
            assert result["Food"]["status"] == "Within Budget"
            assert result["Food"]["difference"] == 2000.0
        finally:
            os.unlink(budget_path)

    def test_on_budget_category(self):
        """Expense == Budget must return 'On Budget'."""
        budget_path = _write_json({"Food": 10000})
        try:
            result = check_budget({"Food": 10000}, budget_path)
            assert result["Food"]["status"] == "On Budget"
            assert result["Food"]["difference"] == 0.0
        finally:
            os.unlink(budget_path)

    def test_sample_data_runs_successfully(self):
        """Ensure it runs against the real sample data file without crashing."""
        # Using real file
        result = check_budget({"Food": 15000, "Transport": 8000}, "data/budget.json")
        assert "Food" in result
        assert "Transport" in result


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestCheckBudgetEdgeCases:

    def test_category_in_expense_but_not_budget(self):
        """If expense exists but no budget limit, limit defaults to 0 -> Overspent."""
        budget_path = _write_json({"Food": 10000})
        try:
            result = check_budget({"Food": 8000, "Unknown": 500}, budget_path)
            assert result["Unknown"]["budget"] == 0.0
            assert result["Unknown"]["status"] == "Overspent"
            assert result["Unknown"]["difference"] == -500.0
        finally:
            os.unlink(budget_path)

    def test_category_in_budget_but_no_expense(self):
        """If budget exists but no expense, expense defaults to 0 -> Within Budget."""
        budget_path = _write_json({"Food": 10000, "Transport": 5000})
        try:
            result = check_budget({"Food": 8000}, budget_path)
            assert result["Transport"]["actual"] == 0.0
            assert result["Transport"]["status"] == "Within Budget"
            assert result["Transport"]["difference"] == 5000.0
        finally:
            os.unlink(budget_path)

    def test_zero_budget_and_zero_expense(self):
        """Zero budget and zero expense -> On Budget."""
        budget_path = _write_json({"WaivedFee": 0})
        try:
            result = check_budget({"WaivedFee": 0}, budget_path)
            assert result["WaivedFee"]["status"] == "On Budget"
        finally:
            os.unlink(budget_path)

    def test_floating_point_precision(self):
        """Float differences must round properly."""
        budget_path = _write_json({"Food": 10000.01})
        try:
            result = check_budget({"Food": 10000.00}, budget_path)
            assert result["Food"]["difference"] == 0.01
        finally:
            os.unlink(budget_path)


# ---------------------------------------------------------------------------
# Negative / security tests
# ---------------------------------------------------------------------------

class TestCheckBudgetNegative:

    def test_raises_file_not_found(self):
        """Must raise FileNotFoundError when budget JSON does not exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            check_budget({"Food": 1000}, "data/nonexistent_budget.json")

    def test_raises_value_error_for_malformed_json(self):
        """Must raise JSONDecodeError when the file is not valid JSON."""
        budget_path = _write_json("{ invalid json, }")
        try:
            with pytest.raises(json.JSONDecodeError):
                check_budget({}, budget_path)
        finally:
            os.unlink(budget_path)

    def test_raises_value_error_if_json_is_list_not_dict(self):
        """Must raise ValueError if JSON root is an array instead of object."""
        budget_path = _write_json([{"Food": 1000}])
        try:
            with pytest.raises(ValueError, match="must be a JSON object"):
                check_budget({}, budget_path)
        finally:
            os.unlink(budget_path)

    def test_raises_value_error_for_non_numeric_budget(self):
        """Must raise ValueError if any budget limit is a string or invalid type."""
        budget_path = _write_json({"Food": "10000"}) # String instead of number
        try:
            with pytest.raises(ValueError, match="must be a number"):
                check_budget({}, budget_path)
        finally:
            os.unlink(budget_path)

    def test_raises_value_error_for_negative_budget(self):
        """Security: Budget limits must not be negative."""
        budget_path = _write_json({"Food": -500})
        try:
            with pytest.raises(ValueError, match="must be non-negative"):
                check_budget({}, budget_path)
        finally:
            os.unlink(budget_path)