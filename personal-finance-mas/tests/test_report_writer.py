"""
test_report_writer.py
~~~~~~~~~~~~~~~~~~~~~
Comprehensive test suite for the report_writer tool (Report Logger Agent).

Covers:
    - Happy path (Markdown generation and trace logging)
    - Edge cases (missing data, empty state)
    - Negative / security tests (unwritable paths)
"""

import json
import os
import tempfile

import pytest

from tools.report_writer import write_report, write_trace_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _temp_file() -> str:
    """Return a path to a non-existent temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
    name = tmp.name
    tmp.close()
    os.unlink(name)
    return name


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestReportWriterHappyPath:

    def test_write_report_with_state(self):
        """Must correctly format full state into Markdown."""
        state = {
            "income_total": 5000.0,
            "expense_total": 2000.0,
            "expense_summary": {"Food": 2000.0},
            "budget_results": {
                "Food": {"actual": 2000.0, "budget": 3000.0, "difference": 1000.0, "status": "Within Budget"}
            },
            "savings_result": {
                "leftover": 3000.0,
                "savings_target": 1200.0,
                "api_context": {"currency_note": "Rate: 300"},
                "llm_advice": "Great job saving!"
            }
        }
        
        path = _temp_file()
        try:
            report_str = write_report(state=state, output_path=path)
            
            assert os.path.exists(path)
            assert "Total Income  | **5,000.00**" in report_str
            assert "Total Expenses | **2,000.00**" in report_str
            assert "🟢 Within Budget" in report_str
            assert "Great job saving!" in report_str
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_write_trace_log(self):
        """Must persist the trace log array to a JSON file."""
        state = {
            "trace_log": [
                {"agent": "Agent1", "status": "success"}
            ]
        }
        
        path = _temp_file()
        try:
            write_trace_log(state, log_path=path)
            
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["agent"] == "Agent1"
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestReportWriterEdgeCases:

    def test_write_report_empty_state_graceful_degradation(self):
        """Must handle empty/missing state variables gracefully (no crash)."""
        state = {} # Empty state
        
        path = _temp_file()
        try:
            report_str = write_report(state=state, output_path=path)
            
            assert "_No expense data available._" in report_str
            assert "_No budget data available._" in report_str
            assert "Total Income  | **0.00**" in report_str
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_write_report_test_mode_kwargs(self):
        """Must support the test-call signature (kwargs instead of state dict)."""
        path = _temp_file()
        try:
            report_str = write_report(
                output_path=path,
                expense_summary={"Food": 100},
                savings_result={"income_total": 100, "expense_total": 100}
            )
            assert "| Food | 100.00 |" in report_str
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_write_trace_log_empty_trace(self):
        """Empty trace log array should still write a valid empty JSON array."""
        state = {"trace_log": []}
        
        path = _temp_file()
        try:
            write_trace_log(state, log_path=path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data == []
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ---------------------------------------------------------------------------
# Negative / security tests
# ---------------------------------------------------------------------------

class TestReportWriterNegative:

    def test_write_report_unwritable_path(self):
        """Security: Attempting to write to a restricted path should bubble up OSError."""
        # /root/ or C:\Windows\System32 is restricted. We use a path that will raise OSError/PermissionError
        unwritable_path = "/invalid_directory_that_does_not_exist/report.md" if os.name != "nt" else "Z:\\invalid_drive\\report.md"
        
        with pytest.raises(OSError):
            write_report(state={}, output_path=unwritable_path)

    def test_write_trace_log_unwritable_path(self):
        """Security: Attempting to write trace to restricted path should raise OSError."""
        unwritable_path = "/invalid_directory_that_does_not_exist/trace.json" if os.name != "nt" else "Z:\\invalid_drive\\trace.json"
        
        with pytest.raises(OSError):
            write_trace_log(state={}, log_path=unwritable_path)