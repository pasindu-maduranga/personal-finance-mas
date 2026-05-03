from typing import Any, Dict

from tools.savings_api import generate_savings_advice
from tools.llm_helper import get_llm_response
from state.shared_state import add_trace


# ---------------------------------------------------------------------------
# Agent Persona
# ---------------------------------------------------------------------------
AGENT_NAME = "Savings Goal Agent"

SYSTEM_PROMPT = """
You are the Savings Goal Agent — a pragmatic personal finance advisor who
specialises in realistic, beginner-friendly savings planning.

Your responsibility is to:
1. Calculate the user's leftover balance after all expenses.
2. Derive a concrete monthly savings target (40 % of leftover).
3. Enrich your recommendation with live currency context from an external API.
4. Generate a short, actionable savings plan using the local phi3 language model.

Constraints:
- Your advice must always be 3–4 sentences — concise and jargon-free.
- If the user is overspending (leftover ≤ 0), you must not fabricate a savings
  target; instead, advise them to cut spending first.
- You must never use hallucinated financial figures — every number is derived
  from the state passed by the Budget Advisor Agent.
- You call the Frankfurter public API for currency context, but you gracefully
  degrade if the API is unavailable.
- You log every action (success or failure) for full observability.
"""


# ---------------------------------------------------------------------------
# Agent entry-point
# ---------------------------------------------------------------------------

def run_savings_goal_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Savings Goal Agent.

    This agent calculates leftover balance, derives a savings target, calls
    the Frankfurter currency API for enrichment, and uses the local phi3 LLM
    to generate a practical savings recommendation.

    Args:
        state: Shared global state dictionary containing income_total and
               expense_total populated by the Expense Tracker Agent.

    Returns:
        Dict[str, Any]: Updated shared state containing:
            - savings_result (dict): savings_target, leftover, advice,
              api_context, llm_advice.

    Raises:
        KeyError: If income_total or expense_total are missing from state.
        RuntimeError: If the LLM call fails.
    """
    print(f"\n[{AGENT_NAME}] Starting - computing savings recommendations")
    print(f"[{AGENT_NAME}] Persona: {SYSTEM_PROMPT.strip().splitlines()[1].strip()}")

    for required_key in ("income_total", "expense_total"):
        if required_key not in state:
            raise KeyError(
                f"[{AGENT_NAME}] '{required_key}' not found in state. "
                "Expense Tracker Agent must run first."
            )

    try:
        result = generate_savings_advice(
            income_total=state["income_total"],
            expense_total=state["expense_total"],
        )

        # Build a precise, constrained prompt aligned with the agent persona
        prompt = f"""{SYSTEM_PROMPT.strip()}

--- FINANCIAL DATA ---
Monthly Income  : {result['income_total']:.2f}
Monthly Expenses: {result['expense_total']:.2f}
Leftover Balance: {result['leftover']:.2f}
Savings Target  : {result['savings_target']:.2f}

Based on the above data, give a short (3-4 sentences), practical, and
beginner-friendly savings recommendation. 
CRITICAL CONSTRAINTS:
1. Do NOT make up numbers.
2. Do NOT apologize.
3. Write ONLY in English. Do NOT translate to any other language.
4. Output ONLY the 3-4 sentence recommendation. No greetings or intros.
"""

        llm_advice = get_llm_response(prompt, model="phi3")
        result["llm_advice"] = llm_advice

        state["savings_result"] = result

        output_summary = (
            f"Leftover: {result['leftover']:.2f} | "
            f"Savings Target: {result['savings_target']:.2f} | "
            f"API: {result['api_context'].get('api_used', 'N/A')} | "
            f"LLM advice generated: {len(llm_advice)} chars"
        )

        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="savings_api.py + llm_helper.py",
            status="success",
            input_summary=(
                f"Income: {state['income_total']:.2f} | "
                f"Expenses: {state['expense_total']:.2f}"
            ),
            output_summary=output_summary,
        )

        print(f"[{AGENT_NAME}] SUCCESS - {output_summary}")

    except Exception as error:
        add_trace(
            state=state,
            agent=AGENT_NAME,
            tool="savings_api.py + llm_helper.py",
            status="failed",
            input_summary=(
                f"Income: {state.get('income_total', 'N/A')} | "
                f"Expenses: {state.get('expense_total', 'N/A')}"
            ),
            output_summary=str(error),
        )
        print(f"[{AGENT_NAME}] FAILED - {error}")
        raise

    return state