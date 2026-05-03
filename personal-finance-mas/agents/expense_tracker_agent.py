from typing import Any, Dict

from tools.csv_reader import read_transactions
from state.shared_state import add_trace


# ---------------------------------------------------------------------------
# Agent Persona
# ---------------------------------------------------------------------------
AGENT_NAME = "Expense Tracker Agent"

SYSTEM_PROMPT = """
You are the Expense Tracker Agent — a meticulous financial data analyst.

Your sole responsibility is to ingest raw transaction data from a CSV file,
validate its integrity, and produce a clean, structured expense summary that
downstream agents can rely on without further validation.

Constraints:
- You must reject any CSV that is missing required columns.
- You must reject any CSV that contains non-numeric amounts.
- You must categorise only rows typed as 'expense' or 'income'.
- You never guess or hallucinate values — every number comes directly from
  the source file.
- You log every action (success or failure) to the shared trace log so the
  system maintains full observability.
"""


# ---------------------------------------------------------------------------
# Agent entry-point
# ---------------------------------------------------------------------------

def run_expense_tracker_agent(
    state: Dict[str, Any],
    csv_path: str,
) -> Dict[str, Any]:
    """
    Run the Expense Tracker Agent.

    This agent reads and validates the transactions CSV, computes per-category
    expense totals, and populates the shared state with structured financial
    data for the Budget Advisor Agent.

    Args:
        state:    Shared global state dictionary passed between agents.
        csv_path: Absolute or relative path to the transactions CSV file.

    Returns:
        Dict[str, Any]: Updated shared state containing:
            - transactions (list[dict])
            - expense_summary (dict[str, float])
            - income_total (float)
            - expense_total (float)

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is malformed or missing required columns.
    """
    print(f"\n[{AGENT_NAME}] Starting - loading transactions from '{csv_path}'")
    print(f"[{AGENT_NAME}] Persona: {SYSTEM_PROMPT.strip().splitlines()[1].strip()}")

    try:
        result = read_transactions(csv_path)

        state["transactions"] = result["transactions"]
        state["expense_summary"] = result["expense_summary"]
        state["income_total"] = result["income_total"]
        state["expense_total"] = result["expense_total"]

        output_summary = (
            f"Loaded {len(result['transactions'])} transactions | "
            f"Income: {result['income_total']:.2f} | "
            f"Expenses: {result['expense_total']:.2f} | "
            f"Categories: {list(result['expense_summary'].keys())}"
        )

        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="csv_reader.py",
            status="success",
            input_summary=f"CSV path: {csv_path}",
            output_summary=output_summary,
        )

        print(f"[{AGENT_NAME}] SUCCESS - {output_summary}")

    except (FileNotFoundError, ValueError) as error:
        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="csv_reader.py",
            status="failed",
            input_summary=f"CSV path: {csv_path}",
            output_summary=str(error),
        )
        print(f"[{AGENT_NAME}] FAILED - {error}")
        raise

    return state