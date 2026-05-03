"""
report_writer.py
~~~~~~~~~~~~~~~~
Custom tool for the Report Logger Agent.

Provides two public functions:
    - write_report()      : Formats shared state into a Markdown finance report.
    - write_trace_log()   : Persists the agent execution trace as JSON.

Both functions include strict type hinting, detailed docstrings, and robust
error handling so the Report Logger Agent can always produce output even when
upstream data is partially missing.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(
    state: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
    expense_summary: Optional[Dict[str, Any]] = None,
    budget_results: Optional[Dict[str, Any]] = None,
    savings_result: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate and write the monthly personal finance Markdown report.

    Supports two call signatures:
        1. System call  — write_report(state)  [used by Report Logger Agent]
        2. Test call    — write_report(output_path=..., expense_summary=..., ...)

    Args:
        state:           Shared global state dict (system call mode).
        output_path:     Destination file path for the report.  Defaults to
                         'outputs/monthly_report.md'.
        expense_summary: Per-category expense totals (test call mode).
        budget_results:  Per-category budget comparison results (test call mode).
        savings_result:  Savings calculation results (test call mode).

    Returns:
        str: The full Markdown report text that was written to disk.

    Raises:
        OSError: If the output file cannot be created or written.
        KeyError: If required keys are missing from the state dict.
    """
    if output_path is None:
        output_path = "outputs/monthly_report.md"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # --- Extract data from state (system) or keyword args (tests) ---
    if state is not None:
        income_total: float = state.get("income_total", 0.0)
        expense_total: float = state.get("expense_total", 0.0)
        expense_summary = state.get("expense_summary", {})
        budget_results = state.get("budget_results", {})
        savings_result = state.get("savings_result", {})
    else:
        expense_summary = expense_summary or {}
        budget_results = budget_results or {}
        savings_result = savings_result or {}
        income_total = savings_result.get("income_total", 0.0)
        expense_total = savings_result.get("expense_total", 0.0)

    leftover: float = savings_result.get("leftover", 0.0)
    savings_target: float = savings_result.get("savings_target", 0.0)
    api_context: Dict[str, Any] = savings_result.get("api_context", {})
    currency_note: str = api_context.get("currency_note", "No currency info available.")
    llm_advice: str = savings_result.get(
        "llm_advice",
        savings_result.get("advice", "No LLM advice available."),
    )

    # --- Build Markdown report ---
    lines = []
    lines.append("# 📊 Monthly Personal Finance Report\n")
    lines.append(f"> Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    lines.append("---\n")
    lines.append("## 💸 Income & Expenses Overview\n")
    lines.append(f"| Metric | Amount |")
    lines.append(f"|---|---|")
    lines.append(f"| Total Income  | **{income_total:,.2f}** |")
    lines.append(f"| Total Expenses | **{expense_total:,.2f}** |")
    lines.append(f"| Net Balance   | **{leftover:,.2f}** |")
    lines.append(f"| Savings Target (40%) | **{savings_target:,.2f}** |\n")

    lines.append("---\n")
    lines.append("## 📂 Expense Summary by Category\n")
    if expense_summary:
        lines.append("| Category | Amount Spent |")
        lines.append("|---|---|")
        for category, amount in sorted(expense_summary.items()):
            lines.append(f"| {category} | {float(amount):,.2f} |")
    else:
        lines.append("_No expense data available._")
    lines.append("")

    lines.append("---\n")
    lines.append("## 📋 Budget Analysis\n")
    if budget_results:
        lines.append("| Category | Actual | Budget | Difference | Status |")
        lines.append("|---|---|---|---|---|")
        for category, result in sorted(budget_results.items()):
            status_icon = (
                "🔴 Overspent" if result["status"] == "Overspent"
                else "🟡 On Budget" if result["status"] == "On Budget"
                else "🟢 Within Budget"
            )
            lines.append(
                f"| {category} "
                f"| {float(result['actual']):,.2f} "
                f"| {float(result['budget']):,.2f} "
                f"| {float(result['difference']):,.2f} "
                f"| {status_icon} |"
            )
    else:
        lines.append("_No budget data available._")
    lines.append("")

    lines.append("---\n")
    lines.append("## 💡 AI-Powered Savings Recommendation\n")
    lines.append(f"**Currency Context:** {currency_note}\n")
    lines.append(f"**phi3 LLM Advice:**\n\n> {llm_advice}\n")

    lines.append("---\n")
    lines.append("_Report generated by the Personal Finance Multi-Agent System (MAS)_")

    report_text = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report_text)

    print(f"[ReportWriter] Report written to: {output_path}")
    return report_text


# ---------------------------------------------------------------------------
# Trace log writer
# ---------------------------------------------------------------------------

def write_trace_log(
    state: Dict[str, Any],
    log_path: Optional[str] = None,
) -> None:
    """
    Persist the agent execution trace log as a structured JSON file.

    The trace log captures every agent's tool calls, inputs, outputs, status,
    and timestamps for full LLMOps observability and auditability.

    Args:
        state:    Shared global state containing the 'trace_log' list.
        log_path: Destination file path for the JSON log.  Defaults to
                  'logs/agent_trace.json'.

    Returns:
        None

    Raises:
        OSError: If the log file cannot be created or written.
    """
    if log_path is None:
        log_path = "logs/agent_trace.json"

    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    trace_log = state.get("trace_log", [])

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(trace_log, file, indent=4, ensure_ascii=False)

    print(f"[ReportWriter] Trace log saved to: {log_path} ({len(trace_log)} entries)")