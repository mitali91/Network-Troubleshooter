"""
troubleshooter.py
Core logic: builds the prompt, calls the Gemini API (free tier),
and parses the structured JSON runbook from the response.
"""

import json
from google import genai
from google.genai import types
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RunbookStep:
    step_number: int
    action: str
    command: Optional[str]
    expected_output: Optional[str]
    if_fails: Optional[str]


@dataclass
class Runbook:
    incident_summary: str
    likely_causes: List[str]
    severity: str          # P1 / P2 / P3
    steps: List[RunbookStep]
    escalation_path: str
    prevention: List[str]
    raw_incident: str


SYSTEM_PROMPT = """You are a senior network engineer with deep expertise in enterprise networking,
cloud infrastructure (AWS, GCP, Azure), BGP/OSPF routing, firewall operations, and data center
networking. You are on-call and have just received a network incident description.

Your job is to generate a concise, structured troubleshooting runbook that a network engineer
can follow step by step.

You MUST respond ONLY with a valid JSON object — no preamble, no explanation, no markdown fences.

The JSON must follow this exact schema:
{
  "incident_summary": "One sentence summarizing the incident",
  "severity": "P1|P2|P3",
  "likely_causes": ["cause 1", "cause 2", "cause 3"],
  "steps": [
    {
      "step_number": 1,
      "action": "What to do and why",
      "command": "exact CLI command or null if not applicable",
      "expected_output": "What you expect to see if healthy, or null",
      "if_fails": "What to do if this step shows a problem, or null"
    }
  ],
  "escalation_path": "Who to escalate to and under what conditions",
  "prevention": ["preventive measure 1", "preventive measure 2"]
}

Severity guidelines:
- P1: Full outage, revenue impact, customer-facing service down
- P2: Degraded service, redundancy lost, partial impact
- P3: Minor issue, no immediate customer impact

Keep steps practical and command-driven. Prefer real CLI commands (Cisco IOS, Linux, AWS CLI)
where applicable. Steps should be ordered from fastest-to-check to most-invasive.
Maximum 8 steps. Return ONLY the JSON object."""


class Troubleshooter:
    """Generates structured network troubleshooting runbooks using Gemini (free tier)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_runbook(self, incident: str) -> Runbook:
        """
        Send incident description to Gemini and return a parsed Runbook.

        Args:
            incident: Natural language description of the network incident.

        Returns:
            Runbook dataclass with structured troubleshooting steps.

        Raises:
            ValueError: If Gemini returns invalid or unparseable JSON.
        """
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,   # low temp = consistent, structured output
            ),
            contents=f"Network incident: {incident}"
        )

        raw_text = response.text.strip()
        return self._parse_response(raw_text, incident)

    def _parse_response(self, raw_text: str, incident: str) -> Runbook:
        """Parse Gemini's JSON response into a Runbook dataclass."""
        # Strip markdown fences if the model adds them despite instructions
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1])

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Model returned invalid JSON.\nRaw response:\n{raw_text}\nError: {e}"
            )

        steps = [
            RunbookStep(
                step_number=s.get("step_number", i + 1),
                action=s.get("action", ""),
                command=s.get("command"),
                expected_output=s.get("expected_output"),
                if_fails=s.get("if_fails"),
            )
            for i, s in enumerate(data.get("steps", []))
        ]

        return Runbook(
            incident_summary=data.get("incident_summary", incident),
            likely_causes=data.get("likely_causes", []),
            severity=data.get("severity", "P2"),
            steps=steps,
            escalation_path=data.get("escalation_path", "Escalate to senior network engineer"),
            prevention=data.get("prevention", []),
            raw_incident=incident,
        )
