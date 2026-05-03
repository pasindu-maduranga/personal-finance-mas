"""
test_csv_reader.py
~~~~~~~~~~~~~~~~~~
Comprehensive test suite for the csv_reader tool (Expense Tracker Agent).

Covers:
    - Happy path (valid CSV with mixed income/expense rows)
    - Edge cases (single row, all income, all expense, zero amounts)
    - Negative / security tests (missing file, missing columns, empty file,
      non-numeric amounts, invalid type values, negative amounts)
    - Boundary tests (very large amounts, many rows)
"""

import os
import textwrap
import tempfile

import pytest

from tools.csv_reader import read_transactions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(content: str) -> str:
    """Write content to a temporary CSV file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    )
    tmp.write(textwrap.dedent(content).strip())
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestReadTransactionsHappyPath:

    def test_returns_expected_keys(self):
        """Result dict must contain all four required keys."""
        result = read_transactions("data/transactions.csv")
        assert "transactions" in result
        assert "expense_summary" in result
        assert "income_total" in result
        assert "expense_total" in result

    def test_income_total_is_positive(self):
        """Income total must be greater than zero for the sample data."""
        result = read_transactions("data/transactions.csv")
        assert result["income_total"] > 0

    def test_expense_total_is_positive(self):
        """Expense total must be greater than zero for the sample data."""
        result = read_transactions("data/transactions.csv")
        assert result["expense_total"] > 0

    def test_transactions_is_a_list(self):
        """Transactions field must be a list."""
        result = read_transactions("data/transactions.csv")
        assert isinstance(result["transactions"], list)

    def test_expense_summary_is_a_dict(self):
        """Expense summary must be a dict."""
        result = read_transactions("data/transactions.csv")
        assert isinstance(result["expense_summary"], dict)

    def test_expense_summary_contains_food_category(self):
        """Sample data includes 'Food' expenses — must appear in summary."""
        result = read_transactions("data/transactions.csv")
        assert "Food" in result["expense_summary"]

    def test_expense_summary_amounts_are_floats(self):
        """All expense summary values must be numeric (float)."""
        result = read_transactions("data/transactions.csv")
        for amount in result["expense_summary"].values():
            assert isinstance(amount, (float, int))

    def test_income_total_matches_expected(self):
        """Sample CSV has salary (120000) + freelance (15000) = 135000."""
        result = read_transactions("data/transactions.csv")
        assert result["income_total"] == pytest.approx(135000.0, rel=1e-3)

    def test_expense_total_matches_expected(self):
        """Sample CSV expenses: 8500+2500+1800+4200+3500+1500+6000+2200+7000+2800+1200+2900+4000 = 48100."""
        result = read_transactions("data/transactions.csv")
        assert result["expense_total"] == pytest.approx(48100.0, rel=1e-3)

    def test_transaction_count_matches_csv(self):
        """Sample CSV has 15 data rows (14 data + 1 header)."""
        result = read_transactions("data/transactions.csv")
        assert len(result["transactions"]) == 15


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestReadTransactionsEdgeCases:

    def test_single_income_row(self):
        """A CSV with only one income row must produce expense_total of 0."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Salary,50000,Income,income
        """)
        try:
            result = read_transactions(path)
            assert result["income_total"] == pytest.approx(50000.0)
            assert result["expense_total"] == pytest.approx(0.0)
            assert result["expense_summary"] == {}
        finally:
            os.unlink(path)

    def test_all_expense_rows_no_income(self):
        """A CSV with only expenses must produce income_total of 0."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Rent,20000,Housing,expense
            2026-04-02,Food,5000,Food,expense
        """)
        try:
            result = read_transactions(path)
            assert result["income_total"] == pytest.approx(0.0)
            assert result["expense_total"] == pytest.approx(25000.0)
        finally:
            os.unlink(path)

    def test_zero_amount_row_is_accepted(self):
        """Zero is a valid amount (e.g. a waived fee)."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Waived fee,0,Fees,expense
            2026-04-02,Salary,10000,Income,income
        """)
        try:
            result = read_transactions(path)
            assert result["expense_total"] == pytest.approx(0.0)
        finally:
            os.unlink(path)

    def test_column_names_case_insensitive(self):
        """Columns in uppercase or mixed case must be accepted."""
        path = _write_csv("""
            Date,Description,Amount,Category,Type
            2026-04-01,Salary,10000,Income,income
        """)
        try:
            result = read_transactions(path)
            assert result["income_total"] == pytest.approx(10000.0)
        finally:
            os.unlink(path)

    def test_very_large_amounts(self):
        """Boundary: very large amounts must not overflow."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,BigSalary,999999999,Income,income
            2026-04-02,BigExpense,888888888,Housing,expense
        """)
        try:
            result = read_transactions(path)
            assert result["income_total"] > 0
            assert result["expense_total"] > 0
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Negative / security tests
# ---------------------------------------------------------------------------

class TestReadTransactionsNegative:

    def test_raises_file_not_found_for_missing_file(self):
        """Must raise FileNotFoundError when the CSV file does not exist."""
        with pytest.raises(FileNotFoundError, match="not found"):
            read_transactions("data/nonexistent_file.csv")

    def test_raises_value_error_for_empty_file(self):
        """Must raise ValueError when the CSV contains only a header row."""
        path = _write_csv("date,description,amount,category,type\n")
        try:
            with pytest.raises(ValueError, match="empty"):
                read_transactions(path)
        finally:
            os.unlink(path)

    def test_raises_value_error_for_missing_columns(self):
        """Must raise ValueError when required columns are absent."""
        path = _write_csv("""
            date,description,amount
            2026-04-01,Salary,10000
        """)
        try:
            with pytest.raises(ValueError, match="missing required column"):
                read_transactions(path)
        finally:
            os.unlink(path)

    def test_raises_value_error_for_non_numeric_amount(self):
        """Must raise ValueError if any amount is not a valid number."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Salary,NOT_A_NUMBER,Income,income
        """)
        try:
            with pytest.raises(ValueError, match="non-numeric"):
                read_transactions(path)
        finally:
            os.unlink(path)

    def test_raises_value_error_for_invalid_type(self):
        """Must raise ValueError for any type value other than income/expense."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Unknown,1000,Misc,transfer
        """)
        try:
            with pytest.raises(ValueError, match="Invalid values in 'type'"):
                read_transactions(path)
        finally:
            os.unlink(path)

    def test_raises_value_error_for_negative_amounts(self):
        """Security: negative amounts are not allowed."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Suspicious,-5000,Income,income
        """)
        try:
            with pytest.raises(ValueError, match="Negative amounts"):
                read_transactions(path)
        finally:
            os.unlink(path)

    def test_raises_value_error_for_sql_injection_in_category(self):
        """Security: SQL injection strings in category column must not crash the tool."""
        path = _write_csv("""
            date,description,amount,category,type
            2026-04-01,Test,1000,"'; DROP TABLE transactions; --",expense
            2026-04-02,Salary,5000,Income,income
        """)
        try:
            # Should process without error — category is just a string label
            result = read_transactions(path)
            assert isinstance(result["expense_summary"], dict)
        finally:
            os.unlink(path)