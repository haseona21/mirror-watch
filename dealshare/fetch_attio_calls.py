"""
fetch_attio_calls.py
--------------------
Fetches calls logged this week from Attio via MCP.
For each deal, extracts: source, company name, one-line description,
team LinkedIn, and raise details from the linked Granola note.

NOTE FOR CLAUDE CODE:
Use the Attio MCP to:
1. Query deals where a meeting/call note was created in the past 7 days
2. For each deal record, extract:
   - source (the Source field on the deal) — display in italics
   - company_name
   - description (one phrase summary)
   - team_linkedin (LinkedIn URLs of founders/team members)
   - raise_details (from the Granola note linked to the deal record)
Return a list of dicts with these keys.
"""


def run() -> list[dict]:
    """
    Returns list of dicts:
    [
      {
        "source": "Cold Inbound",
        "company_name": "Acme",
        "description": "AI-powered logistics",
        "team_linkedin": "https://linkedin.com/in/...",
        "raise_details": "Raising $5M Seed"
      },
      ...
    ]

    NOTE FOR CLAUDE CODE: replace the return below with Attio MCP call results.
    """
    print("📞 Fetching Attio calls this week...")
    # ← Claude Code: use Attio MCP here
    return []
