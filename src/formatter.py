"""
formatter.py
Handles all output: colored terminal display and JSON file export.
"""

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .troubleshooter import Runbook

# ANSI color codes
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
GRAY   = "\033[90m"
WHITE  = "\033[97m"

SEVERITY_COLORS = {
    "P1": RED,
    "P2": YELLOW,
    "P3": GREEN,
}


def colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color}{text}{RESET}"


def severity_badge(severity: str, use_color: bool = True) -> str:
    color = SEVERITY_COLORS.get(severity, WHITE)
    badge = f" {severity} "
    if use_color:
        return f"\033[1m{color}[{badge}]{RESET}"
    return f"[{badge}]"


def print_runbook(runbook: "Runbook", use_color: bool = True) -> None:
    """Print a formatted runbook to stdout."""
    c = lambda text, color: colorize(text, color, use_color)
    sep = c("─" * 60, GRAY)

    print(sep)
    print(c("  NETWORK TROUBLESHOOTING RUNBOOK", BOLD + WHITE))
    print(sep)

    # Header
    print(f"\n{c('INCIDENT', BOLD)}  {runbook.incident_summary}")
    print(f"{c('SEVERITY', BOLD)}  {severity_badge(runbook.severity, use_color)}")
    print(f"{c('GENERATED', BOLD)} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Likely causes
    print(c("LIKELY CAUSES", BOLD + CYAN))
    for i, cause in enumerate(runbook.likely_causes, 1):
        print(f"  {c(str(i) + '.', CYAN)} {cause}")

    # Steps
    print(f"\n{c('TROUBLESHOOTING STEPS', BOLD + CYAN)}")
    for step in runbook.steps:
        print(f"\n  {c(f'Step {step.step_number}', BOLD + WHITE)}  {step.action}")
        if step.command:
            print(f"  {c('Command:', GRAY)}")
            print(f"    {c(step.command, YELLOW)}")
        if step.expected_output:
            print(f"  {c('Expected:', GRAY)} {step.expected_output}")
        if step.if_fails:
            print(f"  {c('If fails:', GRAY)} {c(step.if_fails, RED)}")

    # Escalation
    print(f"\n{sep}")
    print(f"{c('ESCALATION', BOLD + RED)}  {runbook.escalation_path}")

    # Prevention
    if runbook.prevention:
        print(f"\n{c('PREVENTION', BOLD + GREEN)}")
        for item in runbook.prevention:
            print(f"  {c('•', GREEN)} {item}")

    print(f"\n{sep}\n")


def save_runbook(runbook: "Runbook", filepath: str) -> None:
    """Save a runbook to a JSON file."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "incident": runbook.raw_incident,
        "incident_summary": runbook.incident_summary,
        "severity": runbook.severity,
        "likely_causes": runbook.likely_causes,
        "steps": [
            {
                "step_number": s.step_number,
                "action": s.action,
                "command": s.command,
                "expected_output": s.expected_output,
                "if_fails": s.if_fails,
            }
            for s in runbook.steps
        ],
        "escalation_path": runbook.escalation_path,
        "prevention": runbook.prevention,
    }
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
