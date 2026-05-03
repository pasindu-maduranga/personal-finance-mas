from typing import Any, Dict

from tools.report_writer import write_report, write_trace_log
from state.shared_state import add_trace


# ---------------------------------------------------------------------------
# Agent Persona
# ---------------------------------------------------------------------------
AGENT_NAME = "Report Logger Agent"

SYSTEM_PROMPT = """
You are the Report Logger Agent — a precise technical writer and system
auditor responsible for the final stage of the personal finance pipeline.

Your responsibilities are:
1. Compile all structured data from the shared state into a well-formatted
   Markdown monthly finance report.
2. Persist the full agent execution trace log as a structured JSON file so
   the team can audit every agent's actions and tool calls.

Constraints:
- You never modify or re-interpret data — you only format and write what is
  present in the shared state.
- Every report must include: expense summary, budget analysis, savings
  recommendation, LLM advice, and currency context.
- Every trace log must be a valid JSON array with one entry per agent action.
- You are the final agent; you must always run even if upstream agents
  produced partial results (graceful degradation with defaults).
- You log your own completion to the trace before persisting the trace file.
"""


# ---------------------------------------------------------------------------
# Agent entry-point
# ---------------------------------------------------------------------------

def run_report_logger_agent(
    state: Dict[str, Any],
    report_path: str,
    log_path: str,
) -> Dict[str, Any]:
    """
    Run the Report Logger Agent.

    This final agent compiles the shared state into a Markdown report and
    persists the full agent execution trace as a JSON log file.

    Args:
        state:       Shared global state populated by all upstream agents.
        report_path: Destination file path for the Markdown monthly report.
        log_path:    Destination file path for the JSON agent trace log.

    Returns:
        Dict[str, Any]: Updated shared state (unchanged data, trace updated).

    Raises:
        OSError: If the report or log file cannot be written.
    """
    print(f"\n[{AGENT_NAME}] Starting - generating report and saving trace log")
    print(f"[{AGENT_NAME}] Persona: {SYSTEM_PROMPT.strip().splitlines()[1].strip()}")

    try:
        # Write the Markdown report
        write_report(state, output_path=report_path)

        # Log own completion *before* saving the trace so it's included
        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="report_writer.py",
            status="success",
            input_summary="Final shared state received from all upstream agents",
            output_summary=(
                f"Report written to: {report_path} | "
                f"Trace log written to: {log_path} | "
                f"Total trace entries: {len(state.get('trace_log', [])) + 1}"
            ),
        )

        # Persist the trace log
        write_trace_log(state, log_path=log_path)

        print(f"[{AGENT_NAME}] SUCCESS - report saved to '{report_path}' | trace to '{log_path}'")

    except OSError as error:
        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="report_writer.py",
            status="failed",
            input_summary="Final shared state received",
            output_summary=str(error),
        )
        print(f"[{AGENT_NAME}] FAILED - {error}")
        raise

    return state