"""
AI-Assisted Help Desk Ticket Triage Tool

Takes a raw ticket description and uses Claude to:
  1. Classify the likely category (Account/Password, Network/VPN, Hardware,
     Software/Access, Email)
  2. Suggest an urgency level
  3. Recommend first-response troubleshooting steps, grounded in a small
     knowledge base you control (not just whatever the model happens to know)
  4. Flag if this looks like a password reset scenario, and if so, print the
     exact PowerShell command to run against the AD lab toolkit

IMPORTANT - what this tool does NOT do:
This tool does not take any action on its own. It does not touch Active
Directory, reset any password, or modify any account. It only suggests what
a human tech should consider doing next. Every suggestion is meant to be
reviewed by a person before anything happens - that's a deliberate design
choice, not a limitation to apologize for. A help desk automation tool that
acts autonomously on account changes without a human in the loop is a
security risk, not a feature.

Setup:
    pip install anthropic
    Set the ANTHROPIC_API_KEY environment variable with your API key from
    console.anthropic.com (this is separate from a claude.ai login).

Usage:
    python triage.py
    (then type a ticket description when prompted)

    or:
    python triage.py --ticket "user can't log into their email, says password is wrong"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Missing dependency. Run: pip install anthropic")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
KB_PATH = SCRIPT_DIR / "knowledge_base.json"
LOG_PATH = SCRIPT_DIR / "triage-log.jsonl"

# Model used for classification. Swap this for whichever current model
# string your API account has access to - check console.anthropic.com if
# this one isn't available on your account.
MODEL = "claude-sonnet-5"


def load_knowledge_base() -> dict:
    if not KB_PATH.exists():
        print(f"Knowledge base not found at {KB_PATH}")
        sys.exit(1)
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(kb: dict) -> str:
    categories_text = json.dumps(kb["categories"], indent=2)
    return f"""You are a help desk ticket triage assistant. Your job is to classify \
incoming IT support tickets and suggest first-response steps for a human \
technician to review - you do not take any action yourself.

Here is the knowledge base of categories and their standard first-response \
steps. Base your suggested_steps on this knowledge base rather than inventing \
new steps, unless the ticket clearly doesn't fit any category:

{categories_text}

Respond with ONLY a JSON object (no other text) in this exact format:
{{
  "category": "<one of the category names above, or 'Uncategorized'>",
  "urgency": "<Low, Medium, or High>",
  "urgency_reason": "<one sentence explaining the urgency level>",
  "suggested_steps": ["<step 1>", "<step 2>", "..."],
  "is_password_reset_flow": <true or false>
}}

Urgency guidance: High = user is completely blocked from working or this \
affects multiple users (possible outage). Medium = user is impacted but has \
a workaround or it's a single non-critical issue. Low = minor annoyance, \
not blocking work."""


def classify_ticket(client: "anthropic.Anthropic", kb: dict, ticket_text: str) -> dict:
    system_prompt = build_system_prompt(kb)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Ticket: {ticket_text}"}],
    )

    raw_text = response.content[0].text.strip()

    # Models occasionally wrap JSON in markdown fences despite instructions -
    # strip those defensively rather than letting the parse fail.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    return json.loads(raw_text)


def log_result(ticket_text: str, result: dict) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "ticket": ticket_text,
        "result": result,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def print_result(result: dict) -> None:
    print("\n" + "=" * 50)
    print(f"Category:  {result.get('category', 'Unknown')}")
    print(f"Urgency:   {result.get('urgency', 'Unknown')} - {result.get('urgency_reason', '')}")
    print("\nSuggested first-response steps (review before acting):")
    for i, step in enumerate(result.get("suggested_steps", []), start=1):
        print(f"  {i}. {step}")

    if result.get("is_password_reset_flow"):
        print("\n[Password reset flow detected]")
        print("If confirmed, the command to run against the AD lab toolkit is:")
        print('  .\\Reset-HelpDeskPassword.ps1 -Username "<username>" -Unlock')
        print("Replace <username> with the actual account - this is NOT run automatically.")

    print("=" * 50 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-assisted help desk ticket triage")
    parser.add_argument("--ticket", type=str, help="Ticket description text")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY environment variable is not set.")
        print("Get a key from console.anthropic.com and set it before running this.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    kb = load_knowledge_base()

    ticket_text = args.ticket
    if not ticket_text:
        ticket_text = input("Enter the ticket description: ").strip()

    if not ticket_text:
        print("No ticket text provided.")
        sys.exit(1)

    try:
        result = classify_ticket(client, kb, ticket_text)
    except json.JSONDecodeError:
        print("Could not parse the model's response as JSON. Try again - "
              "this can happen occasionally with free-form model output.")
        sys.exit(1)
    except anthropic.APIError as e:
        print(f"API error: {e}")
        sys.exit(1)

    print_result(result)
    log_result(ticket_text, result)


if __name__ == "__main__":
    main()
