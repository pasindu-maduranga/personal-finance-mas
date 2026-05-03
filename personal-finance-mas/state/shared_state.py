from typing import Any, Dict, List


def create_initial_state() -> Dict[str, Any]:
    """
    Create the shared global state used by all agents.

    Returns:
        Dict[str, Any]: Initial shared state dictionary.
    """
    return {
        "transactions": [],
        "expense_summary": {},
        "income_total": 0.0,
        "expense_total": 0.0,
        "budget_results": {},
        "savings_result": {},
        "final_report": "",
        "trace_log": []
    }


def add_trace(
    state: Dict[str, Any],
    agent: str,
    tool: str,
    status: str,
    input_summary: str,
    output_summary: str
) -> None:
    """
    Add a structured log entry to the shared trace log.

    Args:
        state: Shared global state.
        agent: Agent name.
        tool: Tool name used.
        status: success / failed.
        input_summary: Short summary of input.
        output_summary: Short summary of output.
    """
    from datetime import datetime

    state["trace_log"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent,
        "tool": tool,
        "status": status,
        "input_summary": input_summary,
        "output_summary": output_summary
    })