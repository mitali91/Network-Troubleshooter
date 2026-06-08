# 🔧 Network Troubleshooter

An AI-powered CLI tool that takes a network incident description and generates a structured, step-by-step troubleshooting runbook using the [Google Gemini API](https://aistudio.google.com) (free tier — no credit card required).

Built for network engineers who need fast, actionable guidance during on-call incidents — without digging through wikis or tribal knowledge docs.

---

## Demo

```
$ python troubleshoot.py --incident "BGP peer dropped on core-router-01"

🔍  Analyzing incident...
    "BGP peer dropped on core-router-01"

────────────────────────────────────────────────────────────
  NETWORK TROUBLESHOOTING RUNBOOK
────────────────────────────────────────────────────────────

INCIDENT   BGP peer dropped between core-router-01 and ISP edge
SEVERITY   [ P1 ]
GENERATED  2026-05-01 14:35:22

LIKELY CAUSES
  1. Physical link failure or interface flapping on uplink
  2. BGP hold timer expired due to high CPU or packet loss
  3. ISP-side configuration change or maintenance

TROUBLESHOOTING STEPS

  Step 1  Check interface status on core-router-01
  Command:
    show interface GigabitEthernet0/0
  Expected: GigabitEthernet0/0 is up, line protocol is up
  If fails: Check physical cabling and SFP; escalate to DC ops

  Step 2  Verify BGP neighbor state
  Command:
    show bgp summary
  Expected: Neighbor should show Established state
  If fails: Note state (Idle/Active/Connect) and duration

  ... (up to 8 steps)

────────────────────────────────────────────────────────────
ESCALATION  Escalate to ISP NOC if BGP won't re-establish after 15 mins

PREVENTION
  • Enable BGP BFD for faster failure detection
  • Configure BGP route dampening to prevent flapping
────────────────────────────────────────────────────────────
```

---

## Features

- **Three input modes** — inline flag, text file, or interactive step-by-step prompts
- **Structured runbooks** — severity rating (P1/P2/P3), likely causes, ordered steps with CLI commands, expected outputs, and escalation path
- **Real CLI commands** — Cisco IOS, Linux, and AWS CLI commands where applicable
- **Save to JSON** — export runbooks for ticketing systems or post-mortems
- **Colored terminal output** — readable at a glance during incidents, with `--no-color` for logging
- **Unit tested** — parsing logic covered without requiring a live API key
- **Free to run** — uses Gemini 2.0 Flash via Google AI Studio free tier

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/network-troubleshooter.git
cd network-troubleshooter
pip install -r requirements.txt
```

Set your Gemini API key:
```bash
export GEMINI_API_KEY=AIza...
```

Get a **free** API key (no credit card) at [aistudio.google.com](https://aistudio.google.com) → **Get API key**.

---

## Usage

**Inline incident description:**
```bash
python troubleshoot.py --incident "OSPF neighbor flapping on distribution switch SW-03"
```

**From a file:**
```bash
python troubleshoot.py --file examples/bgp_peer_down.txt
```

**Interactive mode** (guided prompts for device, symptom, recent changes):
```bash
python troubleshoot.py --interactive
```

**Save runbook to JSON:**
```bash
python troubleshoot.py --incident "VPC peering packet loss us-east-1" --save runbook.json
```

**Disable color** (useful for logging or piping output):
```bash
python troubleshoot.py --incident "DNS resolution failing" --no-color
```

---

## Example Incidents

The `examples/` folder contains sample incident descriptions you can test with:

```bash
python troubleshoot.py --file examples/bgp_peer_down.txt
python troubleshoot.py --file examples/vpc_peering_latency.txt
```

---

## Running Tests

Unit tests cover JSON parsing, edge cases, and error handling — no API key required.

```bash
pytest tests/ -v
```

---

## Project Structure

```
network-troubleshooter/
├── troubleshoot.py          # CLI entry point (argparse)
├── src/
│   ├── __init__.py
│   ├── troubleshooter.py    # Gemini API integration + runbook parsing
│   └── formatter.py         # Terminal output + JSON export
├── tests/
│   └── test_troubleshooter.py
├── examples/
│   ├── bgp_peer_down.txt
│   └── vpc_peering_latency.txt
├── requirements.txt
└── .gitignore
```

---

## How It Works

1. The incident description is sent to Gemini with a structured system prompt instructing it to respond only with a JSON runbook schema
2. The `Troubleshooter` class parses the JSON into typed Python dataclasses (`Runbook`, `RunbookStep`)
3. The `formatter` module renders the runbook to the terminal with color-coded severity, steps, and commands
4. Optionally, the runbook is serialized back to JSON for export

---

## Tech Stack

- **Python 3.9+**
- **[google-genai](https://github.com/googleapis/python-genai)** — Gemini API client
- **argparse** — CLI interface
- **dataclasses** — typed runbook schema
- **pytest** — unit tests

---

## Author

**Mitali Varerkar** — Senior Cloud Network Engineer  
[linkedin.com/in/mitalivarerkar](https://linkedin.com/in/mitalivarerkar)
