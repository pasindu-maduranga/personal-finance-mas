from orchestrator.workflow import run_workflow


def main() -> None:
    # Use the new scenario 2 data files
    csv_path = "data/transactions_scenario2.csv"
    budget_path = "data/budget_scenario2.json"
    
    # Save to different outputs so we can compare
    report_path = "outputs/monthly_report_scenario2.md"
    log_path = "logs/agent_trace_scenario2.json"

    final_state = run_workflow(
        csv_path=csv_path,
        budget_path=budget_path,
        report_path=report_path,
        log_path=log_path
    )

    print("\n--- SCENARIO 2 EXECUTION COMPLETE ---")
    print(f"Income Total   : {final_state['income_total']}")
    print(f"Expense Total  : {final_state['expense_total']}")
    print(f"Savings Target : {final_state['savings_result']['savings_target']}")
    print(f"Report saved to {report_path}")
    print(f"Trace saved to {log_path}")


if __name__ == "__main__":
    main()
