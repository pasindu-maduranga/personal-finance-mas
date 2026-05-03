from typing import Any, Dict

from langgraph.graph import StateGraph, END

from state.shared_state import create_initial_state
from agents.expense_tracker_agent import run_expense_tracker_agent
from agents.budget_advisor_agent import run_budget_advisor_agent
from agents.savings_goal_agent import run_savings_goal_agent
from agents.report_logger_agent import run_report_logger_agent


# ---------------------------------------------------------------------------
# Node wrapper functions
# LangGraph nodes receive the current state dict and must return a (partial)
# state update dict.  We keep the agents themselves path-agnostic by injecting
# the file paths via closures created inside run_workflow().
# ---------------------------------------------------------------------------

def run_workflow(
    csv_path: str,
    budget_path: str,
    report_path: str,
    log_path: str,
) -> Dict[str, Any]:
    """
    Build and execute the LangGraph StateGraph multi-agent pipeline.

    The graph follows a strict sequential pipeline:
        expense_tracker → budget_advisor → savings_goal → report_logger → END

    Args:
        csv_path:     Path to the transactions CSV file.
        budget_path:  Path to the budget JSON file.
        report_path:  Destination path for the Markdown report.
        log_path:     Destination path for the JSON trace log.

    Returns:
        Dict[str, Any]: The final shared state after all agents have run.
    """

    # --- Node closures (inject file-path dependencies) ---

    def node_expense_tracker(state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node: Expense Tracker Agent."""
        return run_expense_tracker_agent(state, csv_path)

    def node_budget_advisor(state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node: Budget Advisor Agent."""
        return run_budget_advisor_agent(state, budget_path)

    def node_savings_goal(state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node: Savings Goal Agent."""
        return run_savings_goal_agent(state)

    def node_report_logger(state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node: Report Logger Agent."""
        return run_report_logger_agent(state, report_path, log_path)

    # --- Build the StateGraph ---
    graph = StateGraph(dict)

    graph.add_node("expense_tracker", node_expense_tracker)
    graph.add_node("budget_advisor", node_budget_advisor)
    graph.add_node("savings_goal", node_savings_goal)
    graph.add_node("report_logger", node_report_logger)

    # --- Define sequential pipeline edges ---
    graph.set_entry_point("expense_tracker")
    graph.add_edge("expense_tracker", "budget_advisor")
    graph.add_edge("budget_advisor", "savings_goal")
    graph.add_edge("savings_goal", "report_logger")
    graph.add_edge("report_logger", END)

    # --- Compile and invoke ---
    app = graph.compile()

    initial_state = create_initial_state()
    final_state: Dict[str, Any] = app.invoke(initial_state)

    return final_state