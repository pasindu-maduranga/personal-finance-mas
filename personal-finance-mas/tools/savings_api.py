"""
savings_api.py
~~~~~~~~~~~~~~
Custom tool for the Savings Goal Agent.

Computes a savings target from leftover income, enriches the result with
live currency context from the free Frankfurter API, and returns a
structured savings advice dict for the LLM and report stages.
"""

from typing import Any, Dict

import requests


FRANKFURTER_URL = "https://api.frankfurter.app/latest"
SAVINGS_RATE = 0.40          # 40 % of leftover balance
REQUEST_TIMEOUT_SECONDS = 10


def generate_savings_advice(
    income_total: float,
    expense_total: float,
) -> Dict[str, Any]:
    """
    Generate a structured savings recommendation from income and expense totals.

    Steps performed:
        1. Compute leftover balance (income − expenses).
        2. Derive a savings target as 40 % of the leftover balance.
        3. Call the Frankfurter public API for a USD→LKR exchange rate as
           real-world contextual enrichment.
        4. Return all computed values in a structured dict.

    The tool degrades gracefully: if the API is unreachable, a fallback
    message is included in the result without raising an exception.

    Args:
        income_total:  Total monthly income (must be ≥ 0).
        expense_total: Total monthly expenses (must be ≥ 0).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - income_total (float):   Total income passed in.
            - expense_total (float):  Total expenses passed in.
            - leftover (float):       income_total − expense_total.
            - savings_target (float): 40 % of leftover (0 if leftover ≤ 0).
            - advice (str):           Rule-based advice string.
            - api_context (dict):     API name and currency note.

    Raises:
        ValueError: If income_total or expense_total are negative numbers.

    Example:
        >>> result = generate_savings_advice(100000, 60000)
        >>> result["leftover"]
        40000.0
        >>> result["savings_target"]
        16000.0
    """
    if income_total < 0:
        raise ValueError(
            f"income_total must be a non-negative number. Got: {income_total}"
        )
    if expense_total < 0:
        raise ValueError(
            f"expense_total must be a non-negative number. Got: {expense_total}"
        )

    leftover: float = round(income_total - expense_total, 2)

    if leftover <= 0:
        savings_target: float = 0.0
        advice: str = (
            "Your monthly expenses are equal to or exceed your income. "
            "Prioritise cutting non-essential spending before setting a savings goal."
        )
    else:
        savings_target = round(leftover * SAVINGS_RATE, 2)
        advice = (
            f"You have {leftover:,.2f} left after expenses. "
            f"A practical savings target of {savings_target:,.2f} "
            f"({int(SAVINGS_RATE * 100)} % of leftover) is recommended."
        )

    # --- Frankfurter API call (graceful degradation) ---
    api_context: Dict[str, str] = {
        "api_used": "Frankfurter (https://api.frankfurter.app)",
        "currency_note": "Unavailable — API could not be reached.",
    }

    try:
        response = requests.get(
            FRANKFURTER_URL,
            params={"from": "USD", "to": "EUR"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        rate: Any = data.get("rates", {}).get("EUR")

        if rate is not None:
            api_context["currency_note"] = (
                f"Live USD → EUR rate: {rate} "
                f"(source: Frankfurter, date: {data.get('date', 'N/A')})"
            )
        else:
            api_context["currency_note"] = (
                "Frankfurter API responded but EUR rate was not available."
            )

    except requests.exceptions.Timeout:
        api_context["currency_note"] = (
            "Frankfurter API timed out — using rule-based advice only."
        )
    except requests.exceptions.ConnectionError:
        api_context["currency_note"] = (
            "No internet connection — using rule-based advice only."
        )
    except requests.exceptions.RequestException as exc:
        api_context["currency_note"] = f"API error: {exc} — using fallback."

    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "leftover": leftover,
        "savings_target": savings_target,
        "advice": advice,
        "api_context": api_context,
    }