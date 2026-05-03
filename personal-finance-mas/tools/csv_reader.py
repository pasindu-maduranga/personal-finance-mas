"""
csv_reader.py
~~~~~~~~~~~~~
Custom tool for the Expense Tracker Agent.

Reads and validates a transactions CSV file, computes income/expense totals,
and produces a per-category expense summary.

This tool enforces strict data quality constraints so downstream agents always
receive clean, validated financial data.
"""

from typing import Any, Dict, List
import os

import pandas as pd


REQUIRED_COLUMNS: set = {"date", "description", "amount", "category", "type"}
VALID_TYPES: set = {"income", "expense"}


def read_transactions(csv_path: str) -> Dict[str, Any]:
    """
    Read and validate a transactions CSV file, then compute income and
    expense summaries grouped by category.

    This tool enforces all of the following data integrity rules:
        - The file must exist at the given path.
        - All five required columns must be present.
        - The CSV must contain at least one row of data.
        - The 'amount' column must contain only valid numeric values.
        - The 'type' column must contain only 'income' or 'expense' values.

    Args:
        csv_path: Absolute or relative path to the CSV file containing
                  financial transactions.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - transactions (List[dict]): Raw transaction records.
            - expense_summary (Dict[str, float]): Total spent per category.
            - income_total (float): Sum of all income transactions.
            - expense_total (float): Sum of all expense transactions.

    Raises:
        FileNotFoundError: If the CSV file does not exist at csv_path.
        ValueError: If required columns are missing, the file is empty,
                    non-numeric amounts are found, or invalid type values
                    are present.

    Example:
        >>> result = read_transactions("data/transactions.csv")
        >>> result["income_total"]
        135000.0
        >>> result["expense_summary"]["Food"]
        13200.0
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Transactions file not found: '{csv_path}'")

    df: pd.DataFrame = pd.read_csv(csv_path)

    # --- Column validation ---
    missing: set = REQUIRED_COLUMNS - set(df.columns.str.lower())
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {sorted(missing)}. "
            f"Expected columns: {sorted(REQUIRED_COLUMNS)}"
        )

    # Normalise column names to lowercase for consistent access
    df.columns = df.columns.str.lower()

    # --- Empty file guard ---
    if df.empty:
        raise ValueError(
            f"Transaction CSV at '{csv_path}' is empty — no data to process."
        )

    # --- Numeric validation on 'amount' ---
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    invalid_rows: int = df["amount"].isna().sum()
    if invalid_rows > 0:
        raise ValueError(
            f"Found {invalid_rows} row(s) with non-numeric values in the "
            "'amount' column. All amounts must be valid numbers."
        )

    # --- Negative amount guard ---
    if (df["amount"] < 0).any():
        raise ValueError(
            "Negative amounts are not allowed. All transaction amounts must "
            "be positive numbers."
        )

    # --- Type validation ---
    df["type"] = df["type"].str.lower().str.strip()
    invalid_types: pd.Series = ~df["type"].isin(VALID_TYPES)
    if invalid_types.any():
        bad_values: List[str] = df.loc[invalid_types, "type"].unique().tolist()
        raise ValueError(
            f"Invalid values in 'type' column: {bad_values}. "
            f"Allowed values are: {sorted(VALID_TYPES)}"
        )

    # --- Computations ---
    expenses_df: pd.DataFrame = df[df["type"] == "expense"]
    income_df: pd.DataFrame = df[df["type"] == "income"]

    expense_summary: Dict[str, float] = (
        expenses_df.groupby("category")["amount"]
        .sum()
        .round(2)
        .to_dict()
    )

    income_total: float = round(float(income_df["amount"].sum()), 2)
    expense_total: float = round(float(expenses_df["amount"].sum()), 2)

    transactions: List[Dict[str, Any]] = df.to_dict(orient="records")

    return {
        "transactions": transactions,
        "expense_summary": expense_summary,
        "income_total": income_total,
        "expense_total": expense_total,
    }