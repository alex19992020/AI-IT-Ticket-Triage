# AI-Assisted Help Desk Ticket Triage

A command-line tool that takes a raw help desk ticket description and uses
an LLM to classify it, suggest an urgency level, and recommend first-response
troubleshooting steps drawn from a small knowledge base - built as a
follow-up to my PowerShell Help Desk Automation Toolkit.

## What this is (and isn't)

This tool assists a human technician during ticket triage. It does **not**
take any action on its own - it never touches Active Directory, resets a
password, or modifies an account. Every suggestion is meant to be reviewed
by a person before anything happens.

That boundary is intentional, not a limitation. A help desk tool that acts
autonomously on account changes without a human in the loop is a security
risk. This one is scoped to speed up the "what's probably going on and what
should I try first" part of a ticket - the part that's genuinely repetitive
- while leaving every actual account change to a person.

## Setup

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
   (this is separate from a claude.ai login).
2. Install the dependency:
   ```
   pip install -r requirements.txt
   ```
3. Set your API key as an environment variable:
   ```
   # Windows PowerShell
   $env:ANTHROPIC_API_KEY = "your-key-here"

   # macOS/Linux
   export ANTHROPIC_API_KEY="your-key-here"
   ```

## Usage

```
python triage.py
```

Then type a ticket description when prompted. Or pass it directly:

```
python triage.py --ticket "user says they can't connect to the VPN from home"
```

## How it works

- `knowledge_base.json` defines the categories this tool recognizes
  (Account/Password, Network/VPN, Hardware, Software/Access, Email) along
  with standard first-response steps for each.
- `triage.py` sends the ticket text to Claude along with the knowledge base,
  asking it to classify the ticket and ground its suggested steps in that
  knowledge base rather than inventing new ones.
- If the ticket looks like a password reset scenario, the tool prints the
  exact PowerShell command to run against my
  [help desk automation toolkit](https://github.com/alex19992020/PowerShell-IT-automation-toolkit) -
  again, only as a suggestion for a human to confirm and run.
- Every classification is logged to `triage-log.jsonl` with a timestamp, so
  there's a record of what the tool suggested over time.

## Example

```
Enter the ticket description: user forgot their password and is locked out

==================================================
Category:  Account/Password
Urgency:   Medium - user is blocked from work but this is a routine, well-understood fix
Suggested first-response steps (review before acting):
  1. Confirm the exact error message the user sees at login.
  2. Check if the account is locked out (repeated bad password attempts).
  3. Reset the password and force a change at next logon.
  4. Unlock the account if locked.

[Password reset flow detected]
If confirmed, the command to run against the AD lab toolkit is:
  .\\Reset-HelpDeskPassword.ps1 -Username "<username>" -Unlock
Replace <username> with the actual account - this is NOT run automatically.
==================================================
```

## Limitations

- Classification quality depends on how clearly the ticket is written -
  vague tickets get vague classifications.
- This has no memory between runs beyond the log file - each ticket is
  classified independently.
- The knowledge base is intentionally small right now (5 categories). A
  production version would need input from an actual IT team's ticket
  history to be genuinely useful.

*(Testing screenshots go here.)*

<img width="1108" height="621" alt="image" src="https://github.com/user-attachments/assets/8e9a99d1-1e99-4bc1-b3bf-091356197cd4" />

My next step was to set my API key that I created on anthropic using the command "$env:ANTHROPIC_API_KEY = "xxxxxxxxxxxxxxxxxxxxxx"".
I then ran my first test to make sure it worked using the command, "python triage.py --ticket "user can't log into their email, password not working"". Shown below.
<img width="1254" height="364" alt="image" src="https://github.com/user-attachments/assets/296c3b48-6969-407c-8e5e-bf8a49ba2c06" />
The result was a clean, correct classification end to end — the right category, sound urgency reasoning, first-response steps pulled directly from the knowledge base, and the password-reset flow correctly triggering the tie-in to the PowerShell toolkit.

During testing, an error surfaced where the model occasionally returned a non-text content block ahead of the text response, which crashed the response parsing. This was fixed and pushed as a follow-up commit. Shown below.
<img width="734" height="423" alt="image" src="https://github.com/user-attachments/assets/d35b4d92-bf97-4461-8451-31a5cb9adcd4" />

I will run 3 tests, "python triage.py --ticket "user says they can't connect to the VPN from home"" "python triage.py --ticket "printer on the 3rd floor isn't printing"" "python triage.py --ticket "my computer is being weird"". Notice how my last test is vague, I want to see whether my AI model forces a category anyway or handles the ambiguity gracefully, since real tickets are often written just as vaguely. Testing across ticket categories confirmed accurate classification. The VPN and printer tests both categorized correctly, with urgency reasoning based on actual impact rather than keyword matching Results shown below. 
<img width="1364" height="790" alt="image" src="https://github.com/user-attachments/assets/d812f70e-21a2-4846-ab47-7165e9dbf96e" />

The VPN and printer tickets were both categorized correctly, with urgency reasoning based on real impact analysis rather than keyword matching — the printer ticket was rated Medium rather than High, with the reasoning that other printers nearby likely provide a workaround. That's the kind of judgment call a real Tier 1 tech would make.

The vague ticket produced the most useful result. Rather than forcing it into one of the five categories, the tool returned Uncategorized, set urgency to Low, and generated steps aimed at gathering more information instead of applying troubleshooting steps that might not even apply. I'd rather the tool admit it doesn't have enough information than project false confidence on unclear input — this result is the clearest evidence of that design goal actually holding up in practice.





