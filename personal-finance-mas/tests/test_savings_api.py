"""
test_savings_api.py
~~~~~~~~~~~~~~~~~~~
Comprehensive test suite for the savings_api tool (Savings Goal Agent).

Covers:
    - Happy path (normal leftover -> 40% target)
    - Edge cases (leftover == 0, fallback to rule-based when API fails)
    - Negative / security tests (negative income, negative expenses)
"""

from unittest.mock import patch

import pytest
import requests

from tools.savings_api import generate_savings_advice


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestGenerateSavingsAdviceHappyPath:

    @patch("tools.savings_api.requests.get")
    def test_normal_leftover_generates_40_percent_target(self, mock_get):
        """Leftover > 0 should yield a target of 40%."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"rates": {"EUR": 0.9}, "date": "2026-05-01"}
        
        result = generate_savings_advice(income_total=100000, expense_total=60000)
        
        assert result["leftover"] == 40000.0
        assert result["savings_target"] == 16000.0  # 40% of 40000
        assert "A practical savings target of 16,000.00" in result["advice"]
        assert "Live USD → EUR rate" in result["api_context"]["currency_note"]

    @patch("tools.savings_api.requests.get")
    def test_large_amounts_handled_correctly(self, mock_get):
        """Boundary: Very large amounts should compute accurately."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"rates": {"EUR": 0.9}}

        result = generate_savings_advice(income_total=999999999, expense_total=555555555)
        
        assert result["leftover"] == 444444444.0
        assert result["savings_target"] == 177777777.6


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestGenerateSavingsAdviceEdgeCases:

    @patch("tools.savings_api.requests.get")
    def test_zero_leftover(self, mock_get):
        """When income == expenses, target must be 0 and advise to cut spending."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"rates": {"EUR": 0.9}}

        result = generate_savings_advice(income_total=50000, expense_total=50000)
        
        assert result["leftover"] == 0.0
        assert result["savings_target"] == 0.0
        assert "equal to or exceed your income" in result["advice"]

    @patch("tools.savings_api.requests.get")
    def test_negative_leftover_overspending(self, mock_get):
        """When expenses > income, target must be 0 and advise to cut spending."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"rates": {"EUR": 0.9}}

        result = generate_savings_advice(income_total=50000, expense_total=80000)
        
        assert result["leftover"] == -30000.0
        assert result["savings_target"] == 0.0
        assert "equal to or exceed your income" in result["advice"]

    @patch("tools.savings_api.requests.get")
    def test_api_timeout_fallback(self, mock_get):
        """If Frankfurter API times out, it should degrade gracefully without crashing."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout occurred")

        result = generate_savings_advice(income_total=100000, expense_total=60000)
        
        assert result["savings_target"] == 16000.0
        assert "API timed out" in result["api_context"]["currency_note"]

    @patch("tools.savings_api.requests.get")
    def test_api_connection_error_fallback(self, mock_get):
        """If internet is down, it should degrade gracefully."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = generate_savings_advice(income_total=100000, expense_total=60000)
        
        assert "No internet connection" in result["api_context"]["currency_note"]

    @patch("tools.savings_api.requests.get")
    def test_api_returns_missing_currency(self, mock_get):
        """If API succeeds but EUR is not in the rates dictionary."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"rates": {"GBP": 0.8}} # Missing EUR

        result = generate_savings_advice(income_total=100000, expense_total=60000)
        
        assert "EUR rate was not available" in result["api_context"]["currency_note"]


# ---------------------------------------------------------------------------
# Negative / security tests
# ---------------------------------------------------------------------------

class TestGenerateSavingsAdviceNegative:

    def test_raises_value_error_for_negative_income(self):
        """Security/Validation: Income cannot be a negative number."""
        with pytest.raises(ValueError, match="income_total must be a non-negative"):
            generate_savings_advice(income_total=-5000, expense_total=2000)

    def test_raises_value_error_for_negative_expense(self):
        """Security/Validation: Expenses cannot be a negative number."""
        with pytest.raises(ValueError, match="expense_total must be a non-negative"):
            generate_savings_advice(income_total=5000, expense_total=-2000)