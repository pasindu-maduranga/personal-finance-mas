from typing import Any, Dict

from tools.budget_checker import check_budget
from state.shared_state import add_trace


# ---------------------------------------------------------------------------
# Agent Persona
# ---------------------------------------------------------------------------
AGENT_NAME = "Budget Advisor Agent"

SYSTEM_PROMPT = """
You are the Budget Advisor Agent — a disciplined financial compliance officer.

Your responsibility is to compare every actual expense category against the
pre-defined budget limits set by the user.  You produce a precise, category-by-
category verdict — Within Budget, On Budget, or Overspent — so that the Savings
Goal Agent can compute realistic savings targets.

Constraints:
- You compare ONLY categories present in either the expense summary or the budget.
- You never modify original expense or budget values; you only compute differences.
- You must flag every overspent category clearly so the reporting agent can
  highlight them in the final report.
- You rely exclusively on the structured expense summary passed from the Expense
  Tracker Agent — you never re-read the CSV yourself.
- You log every action (success or failure) so the system maintains full
  observability.
"""


# ---------------------------------------------------------------------------
# Agent entry-point
# ---------------------------------------------------------------------------

def run_budget_advisor_agent(
    state: Dict[str, Any],
    budget_path: str,
) -> Dict[str, Any]:
    """
    Run the Budget Advisor Agent.

    This agent reads the budget JSON, compares each expense category against
    its allowed budget limit, and produces a structured comparison result.
    The result is stored in the shared state for the Savings Goal Agent.

    Args:
        state:       Shared global state dictionary passed between agents.
        budget_path: Absolute or relative path to the budget JSON file.

    Returns:
        Dict[str, Any]: Updated shared state containing:
            - budget_results (dict[str, dict]):
                Each key is a category; each value contains actual, budget,
                difference, and status fields.

    Raises:
        FileNotFoundError: If the budget JSON file does not exist.
        ValueError: If the budget JSON is malformed.
        KeyError: If the expense_summary key is missing from state.
    """
    print(f"\n[{AGENT_NAME}] Starting - comparing expenses against budget '{budget_path}'")
    print(f"[{AGENT_NAME}] Persona: {SYSTEM_PROMPT.strip().splitlines()[1].strip()}")

    if "expense_summary" not in state:
        raise KeyError(
            f"[{AGENT_NAME}] 'expense_summary' not found in state. "
            "Expense Tracker Agent must run first."
        )

    try:
        results = check_budget(state["expense_summary"], budget_path)
        state["budget_results"] = results

        overspent = [cat for cat, data in results.items() if data["status"] == "Overspent"]
        within = [cat for cat, data in results.items() if data["status"] == "Within Budget"]

        output_summary = (
            f"Checked {len(results)} categories | "
            f"Overspent: {overspent if overspent else 'None'} | "
            f"Within Budget: {len(within)}"
        )

        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="budget_checker.py",
            status="success",
            input_summary=f"Budget path: {budget_path} | Categories: {list(state['expense_summary'].keys())}",
            output_summary=output_summary,
        )

        print(f"[{AGENT_NAME}] SUCCESS - {output_summary}")

    except (FileNotFoundError, ValueError) as error:
        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="budget_checker.py",
            status="failed",
            input_summary=f"Budget path: {budget_path}",
            output_summary=str(error),
        )
        print(f"[{AGENT_NAME}] FAILED - {error}")
        raise

    return state