from orchestrator.workflow import run_workflow


def main() -> None:
    csv_path = "data/transactions.csv"
    budget_path = "data/budget.json"
    report_path = "outputs/monthly_report.md"
    log_path = "logs/agent_trace.json"

    final_state = run_workflow(
        csv_path=csv_path,
        budget_path=budget_path,
        report_path=report_path,
        log_path=log_path
    )

    print("\nSystem completed successfully.")
    print(f"Income Total   : {final_state['income_total']}")
    print(f"Expense Total  : {final_state['expense_total']}")
    print(f"Savings Target : {final_state['savings_result']['savings_target']}")
    print("Report saved to outputs/monthly_report.md")
    print("Trace saved to logs/agent_trace.json")


if __name__ == "__main__":
    main()