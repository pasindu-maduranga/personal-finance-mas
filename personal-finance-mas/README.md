# AI-Powered Personal Finance Multi-Agent System

## Project Overview
This project is a locally hosted Multi-Agent System (MAS) developed for the CTSE Assignment 2.  
It automates a personal finance workflow by using multiple agents that collaborate with one another to process transactions, compare expenses against a budget, generate savings recommendations, and produce a final report.

The system runs fully locally and uses:
- Python
- LangGraph-style orchestration
- Custom Python tools
- Ollama with the `phi3` local language model
- Logging and tracing
- Automated tests with pytest

---

## Problem Domain
Managing monthly personal finances can be difficult when users need to:
- track income and expenses,
- compare expenses against planned budgets,
- identify overspending,
- decide how much to save,
- summarize everything in a clean report.

This system solves that problem through a pipeline of specialized agents.

---

## System Architecture

### Agents
1. **Expense Tracker Agent**
   - Reads transaction data from a CSV file
   - Calculates total income and expenses
   - Produces expense summaries by category

2. **Budget Advisor Agent**
   - Reads budget data from a JSON file
   - Compares actual expenses against budget allocations
   - Detects overspending and under-budget categories

3. **Savings Goal Agent**
   - Calculates leftover balance
   - Uses a free public API for contextual financial information
   - Uses the local `phi3` model via Ollama to generate practical savings advice

4. **Report Logger Agent**
   - Generates a Markdown monthly report
   - Saves a JSON trace log of the agent workflow

---

## Workflow

```text
transactions.csv
      ↓
Expense Tracker Agent
      ↓
Budget Advisor Agent
      ↓
Savings Goal Agent
      ↓
Report Logger Agent
      ↓
monthly_report.md + agent_trace.json