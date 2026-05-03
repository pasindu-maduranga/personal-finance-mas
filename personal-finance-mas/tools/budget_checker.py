"""
budget_checker.py
~~~~~~~~~~~~~~~~~
Custom tool for the Budget Advisor Agent.

Loads a budget allocation JSON file and compares each category's actual
spending against its allocated limit.  Returns a structured verdict for
every category so the Savings Goal Agent and Report Logger Agent can
make informed decisions.
"""

import json
import os
from typing import Dict, Union


BudgetResult = Dict[str, Union[float, str]]


def check_budget(
    expense_summary: Dict[str, float],
    budget_path: str,
) -> Dict[str, BudgetResult]:
    """
    Compare actual category expenses against their budget allocations.

    For each category present in either the expense summary or the budget
    file, this tool calculates the actual spend, the allocated limit, the
    monetary difference, and a human-readable status verdict.

    Status verdicts:
        - "Overspent"     : actual > budget limit
        - "On Budget"     : actual == budget limit (exactly)
        - "Within Budget" : actual < budget limit

    Args:
        expense_summary: Dict mapping category names to their total actual
                         spend (e.g. {"Food": 13200.0, "Transport": 9500.0}).
        budget_path:     Absolute or relative path to a JSON file mapping
                         category names to their budget limits
                         (e.g. {"Food": 12000, "Transport": 8000}).

    Returns:
        Dict[str, BudgetResult]: A dict where each key is a category name
        and each value contains:
            - actual (float):     Total actual spend for the category.
            - budget (float):     Allocated budget limit.
            - difference (float): budget − actual (negative = overspent).
            - status (str):       "Overspent" | "On Budget" | "Within Budget".

    Raises:
        FileNotFoundError: If the budget JSON file does not exist.
        ValueError: If the JSON content is not a dict, or contains
                    non-numeric budget values.
        json.JSONDecodeError: If the file is not valid JSON.

    Example:
        >>> result = check_budget({"Food": 13200}, "data/budget.json")
        >>> result["Food"]["status"]
        'Overspent'
    """
    if not os.path.exists(budget_path):
        raise FileNotFoundError(f"Budget file not found: '{budget_path}'")

    with open(budget_path, "r", encoding="utf-8") as file:
        budgets: object = json.load(file)

    if not isinstance(budgets, dict):
        raise ValueError(
            f"Budget JSON at '{budget_path}' must be a JSON object (dict). "
            f"Got: {type(budgets).__name__}"
        )

    # --- Validate all budget values are numeric ---
    for category, limit in budgets.items():
        if not isinstance(limit, (int, float)):
            raise ValueError(
                f"Budget value for category '{category}' must be a number. "
                f"Got: {type(limit).__name__} = {limit!r}"
            )
        if limit < 0:
            raise ValueError(
                f"Budget value for category '{category}' must be non-negative. "
                f"Got: {limit}"
            )

    results: Dict[str, BudgetResult] = {}
    all_categories = sorted(
        set(expense_summary.keys()) | set(budgets.keys())
    )

    for category in all_categories:
        actual: float = round(float(expense_summary.get(category, 0.0)), 2)
        limit: float = round(float(budgets.get(category, 0.0)), 2)
        difference: float = round(limit - actual, 2)

        if actual > limit:
            status = "Overspent"
        elif actual == limit:
            status = "On Budget"
        else:
            status = "Within Budget"

        results[category] = {
            "actual": actual,
            "budget": limit,
            "difference": difference,
            "status": status,
        }

    return results