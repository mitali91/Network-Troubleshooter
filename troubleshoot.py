#!/usr/bin/env python3
"""
network-troubleshooter: AI-powered network incident runbook generator.
Uses Google Gemini API (free tier) to analyze network incidents and return
structured, actionable troubleshooting runbooks.

Usage:
    python troubleshoot.py --incident "BGP peer dropped on core-router-01"
    python troubleshoot.py --file examples/sample_incident.txt
    python troubleshoot.py --interactive
"""

import argparse
import sys
import os
from src.troubleshooter import Troubleshooter
from src.formatter import print_runbook, save_runbook


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-powered network incident troubleshooter using Gemini API (free tier)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python troubleshoot.py --incident "BGP peer dropped on core-router-01"
  python troubleshoot.py --file examples/bgp_peer_down.txt
  python troubleshoot.py --interactive
  python troubleshoot.py --incident "OSPF adjacency flapping" --save output.json
        """
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--incident", "-i",
        type=str,
        help="Describe the network incident in quotes"
    )
    group.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a text file containing the incident description"
    )
    group.add_argument(
        "--interactive",
        action="store_true",
        help="Enter interactive mode to describe incident step by step"
    )
    parser.add_argument(
        "--save", "-s",
        type=str,
        help="Save the runbook to a JSON file (optional)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output"
    )
    return parser.parse_args()


def get_incident_from_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    with open(filepath, "r") as f:
        content = f.read().strip()
    if not content:
        print("Error: Incident file is empty.")
        sys.exit(1)
    return content


def interactive_mode() -> str:
    print("\n=== Network Troubleshooter — Interactive Mode ===\n")
    print("Answer the following questions to build your incident description.")
    print("Press Enter to skip any question.\n")

    questions = [
        ("What device or system is affected?", "e.g. core-router-01, switch-nyc-03"),
        ("What is the symptom or alert?",       "e.g. BGP peer down, high latency, packet loss"),
        ("When did it start?",                  "e.g. 10 minutes ago, after maintenance window"),
        ("Any recent changes made?",            "e.g. config push, firmware upgrade, circuit change"),
        ("What have you already tried?",        "e.g. checked interface status, ping tests"),
        ("Any relevant error messages or logs?","paste a snippet if available"),
    ]

    answers = []
    for question, hint in questions:
        print(f"  {question}")
        print(f"  ({hint})")
        answer = input("  > ").strip()
        if answer:
            answers.append(f"{question} {answer}")
        print()

    if not answers:
        print("Error: No incident details provided.")
        sys.exit(1)

    return " | ".join(answers)


def main():
    args = parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\nError: GEMINI_API_KEY environment variable not set.")
        print("  Export your key:  export GEMINI_API_KEY=AIza...")
        print("  Get a free key at: https://aistudio.google.com\n")
        sys.exit(1)

    # Get incident description
    if args.incident:
        incident = args.incident
    elif args.file:
        incident = get_incident_from_file(args.file)
    else:
        incident = interactive_mode()

    print("\n🔍  Analyzing incident...")
    print(f"    \"{incident[:100]}{'...' if len(incident) > 100 else ''}\"\n")

    troubleshooter = Troubleshooter(api_key=api_key)

    try:
        runbook = troubleshooter.generate_runbook(incident)
    except Exception as e:
        print(f"\nError calling Gemini API: {e}")
        sys.exit(1)

    print_runbook(runbook, use_color=not args.no_color)

    if args.save:
        save_runbook(runbook, args.save)
        print(f"\n✅  Runbook saved to: {args.save}")


if __name__ == "__main__":
    main()
