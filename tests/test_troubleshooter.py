"""
tests/test_troubleshooter.py
Unit tests for the Troubleshooter class — tests parsing logic
without making real API calls (no API key required).
"""

import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.troubleshooter import Troubleshooter, Runbook, RunbookStep


MOCK_RESPONSE = {
    "incident_summary": "BGP peer dropped between core-router-01 and ISP edge router",
    "severity": "P1",
    "likely_causes": [
        "Physical link failure or flapping on uplink interface",
        "BGP hold timer expired due to high CPU or packet loss",
        "ISP-side configuration change or maintenance"
    ],
    "steps": [
        {
            "step_number": 1,
            "action": "Check interface status on core-router-01",
            "command": "show interface GigabitEthernet0/0",
            "expected_output": "GigabitEthernet0/0 is up, line protocol is up",
            "if_fails": "If interface is down, check physical cabling and SFP; escalate to DC ops"
        },
        {
            "step_number": 2,
            "action": "Verify BGP neighbor state",
            "command": "show bgp summary",
            "expected_output": "Neighbor should show Established state",
            "if_fails": "Note the state (Idle/Active/Connect) and how long it has been in that state"
        }
    ],
    "escalation_path": "Escalate to ISP NOC if interface is up but BGP session won't establish after 15 minutes",
    "prevention": [
        "Enable BGP BFD for faster failure detection",
        "Configure BGP route dampening to prevent flapping"
    ]
}


class MockTroubleshooter(Troubleshooter):
    """Subclass that bypasses the real API for testing."""

    def __init__(self):
        self.model = "gemini-2.0-flash"

    def generate_runbook(self, incident: str) -> Runbook:
        raw = json.dumps(MOCK_RESPONSE)
        return self._parse_response(raw, incident)


class TestRunbookParsing:

    def setup_method(self):
        self.ts = MockTroubleshooter()

    def test_returns_runbook_instance(self):
        runbook = self.ts.generate_runbook("BGP peer dropped on core-router-01")
        assert isinstance(runbook, Runbook)

    def test_incident_summary_parsed(self):
        runbook = self.ts.generate_runbook("test incident")
        assert "BGP" in runbook.incident_summary

    def test_severity_parsed(self):
        runbook = self.ts.generate_runbook("test incident")
        assert runbook.severity == "P1"

    def test_likely_causes_are_list(self):
        runbook = self.ts.generate_runbook("test incident")
        assert isinstance(runbook.likely_causes, list)
        assert len(runbook.likely_causes) == 3

    def test_steps_parsed_correctly(self):
        runbook = self.ts.generate_runbook("test incident")
        assert len(runbook.steps) == 2
        assert isinstance(runbook.steps[0], RunbookStep)

    def test_step_fields_populated(self):
        runbook = self.ts.generate_runbook("test incident")
        step = runbook.steps[0]
        assert step.step_number == 1
        assert step.command is not None
        assert step.expected_output is not None
        assert step.if_fails is not None

    def test_prevention_is_list(self):
        runbook = self.ts.generate_runbook("test incident")
        assert isinstance(runbook.prevention, list)
        assert len(runbook.prevention) == 2

    def test_raw_incident_preserved(self):
        incident = "OSPF neighbor flapping on core switch"
        runbook = self.ts.generate_runbook(incident)
        assert runbook.raw_incident == incident

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            self.ts._parse_response("this is not json", "test incident")

    def test_markdown_fences_stripped(self):
        fenced = "```json\n" + json.dumps(MOCK_RESPONSE) + "\n```"
        runbook = self.ts._parse_response(fenced, "test")
        assert runbook.severity == "P1"

    def test_severity_p2(self):
        data = {**MOCK_RESPONSE, "severity": "P2"}
        runbook = self.ts._parse_response(json.dumps(data), "test")
        assert runbook.severity == "P2"

    def test_empty_steps_handled(self):
        data = {**MOCK_RESPONSE, "steps": []}
        runbook = self.ts._parse_response(json.dumps(data), "test")
        assert runbook.steps == []

    def test_null_command_handled(self):
        data = {**MOCK_RESPONSE}
        data["steps"][0]["command"] = None
        runbook = self.ts._parse_response(json.dumps(data), "test")
        assert runbook.steps[0].command is None
