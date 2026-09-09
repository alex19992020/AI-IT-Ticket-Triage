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
Here is me creating my claude API below,

<img width="1433" height="263" alt="image" src="https://github.com/user-attachments/assets/c0adb573-177f-4bb5-84fd-22f32f76b2fa" />

Ok, now I will go into my files using the powershell in order to follow the steps required to download everything from the readme. Shown below.
<img width="1107" height="621" alt="image" src="https://github.com/user-attachments/assets/c354c1b9-84ea-49d5-9748-1d6412bae453" />

Next I will install the dependency using the command "pip install -r requirements.txt", Shown below.
<img width="1108" height="621" alt="image" src="https://github.com/user-attachments/assets/8e9a99d1-1e99-4bc1-b3bf-091356197cd4" />

My next step was to set my API key that I created on anthropic using the command "$env:ANTHROPIC_API_KEY = "xxxxxxxxxxxxxxxxxxxxxx"".
I then ran my first test to make sure it worked using the command, "python triage.py --ticket "user can't log into their email, password not working"". Shown below.
<img width="1254" height="364" alt="image" src="https://github.com/user-attachments/assets/296c3b48-6969-407c-8e5e-bf8a49ba2c06" />
This shows a clean, correct result end to end — right category, reasonable urgency reasoning, steps pulled straight from the knowledge base, and the password-reset tie-in triggered exactly as designed. The whole pipeline being API key → script → knowledge base → structured output is proven to work correctly. I will run other tests to further test to see how it handles vague tickets.

I did run into a couple of errors involving response parsing with non text content blocks that I fixed. After I did a git pull then git push so that it would be updated on my github. Shown below.
<img width="734" height="423" alt="image" src="https://github.com/user-attachments/assets/d35b4d92-bf97-4461-8451-31a5cb9adcd4" />

Ok, now I will run more tests to see how good my AI model categorizes tickets, I will run 3 tests, "python triage.py --ticket "user says they can't connect to the VPN from home"" "python triage.py --ticket "printer on the 3rd floor isn't printing"" "python triage.py --ticket "my computer is being weird"". Notice how my last test is vague, I want to see whether my AI model forces a category anyway or handles the ambiguity gracefully, since real tickets are often written just as vaguely. Results shown below.
<img width="1364" height="790" alt="image" src="https://github.com/user-attachments/assets/d812f70e-21a2-4846-ab47-7165e9dbf96e" />

These were very good results because VPN and printer tests: both categorized correctly, and the urgency reasoning is doing real analysis, not just keyword matching. As you can see, the printer ticket got Medium, not High, with the reasoning "affects multiple users but likely has workarounds like other printers nearby" — that's the model weighing impact against available alternatives, which is exactly the judgment call a real Tier 1 tech would make.

The third test, that being my vague test, also gave a good result because instead of forcing that into one of your five categories just because it had to pick something, it correctly returned Uncategorized, set urgency to low with the reasoning that there's not enough information yet, and generated steps aimed at gathering more detail rather than pulling generic troubleshooting steps that wouldn't actually apply. That shows that my AI tool is correctly recognizing the limits of what it can determine from a bad ticket description, instead of confidently guessing wrong. I'll rather my AI tool admit it doesn't have enough information then admit fake confidence on unclear unput.





