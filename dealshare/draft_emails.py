"""
draft_emails.py
---------------
Fetches the Dealshare list from Attio (filtered to "Mae to Draft Email" = true),
shows a confirmation prompt, then creates Gmail drafts for each recipient.

NOTE FOR CLAUDE CODE:
- Use Attio MCP to fetch people on the "Dealshare" list where "Mae to Draft Email" = true
- Use Gmail MCP to search prior threads per recipient for brief context
- Use Gmail MCP to create drafts
"""


def strip_markdown(content: str) -> str:
    """Convert markdown to plain text for email body."""
    lines = []
    for line in content.split("\n"):
        if line.startswith("# "):
            continue  # skip file title
        line = line.replace("**", "")  # remove bold markers
        lines.append(line)
    return "\n".join(lines).strip()


def build_email_body(first_name: str, markdown_content: str, prior_context: str = "") -> str:
    plain = strip_markdown(markdown_content)
    body = f"{first_name}, sharing folks we recently met and deals we recently heard about."
    if prior_context:
        body += f"\n\n{prior_context}"
    body += f"\n\n{plain}"
    return body


def run(markdown_content: str):
    """
    Fetches Dealshare recipients, confirms, creates Gmail drafts.

    NOTE FOR CLAUDE CODE:
    1. Use Attio MCP to fetch people on the "Dealshare" list
       where "Mae to Draft Email" = true
       Extract: first_name, last_name, email_address
    2. Show confirmation prompt (code below handles this)
    3. For each person:
       - Use Gmail MCP to search their name/email for prior thread context
       - Build email body
       - Use Gmail MCP to create draft
    """
    print("\n📋 Fetching Dealshare list from Attio...")

    # ← Claude Code: replace with Attio MCP call
    # Filter: list = "Dealshare", "Mae to Draft Email" = true
    dealshare_recipients = []

    if not dealshare_recipients:
        print("⚠️  No recipients found. Check Attio Dealshare list.")
        return

    # ── Confirmation prompt ───────────────────────────────────────────────────
    print(f"\nReady to create Gmail drafts for {len(dealshare_recipients)} people:\n")
    for person in dealshare_recipients:
        first = person.get("first_name", "")
        last = person.get("last_name", "")
        email = person.get("email_address", "")
        print(f"  - {first} {last} ({email})")

    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled. No drafts created.")
        return

    # ── Create drafts ─────────────────────────────────────────────────────────
    print("\n📧 Creating Gmail drafts...")
    for person in dealshare_recipients:
        first_name = person.get("first_name", "there")
        email = person.get("email_address", "")

        # ← Claude Code: use Gmail MCP to search prior thread for context
        # Search query: from:{email} OR to:{email}
        # If something relevant found, extract a brief note. Otherwise leave blank.
        prior_context = ""

        body = build_email_body(first_name, markdown_content, prior_context)

        # ← Claude Code: use Gmail MCP to create draft
        # gmail_mcp.create_draft(to=email, subject="", body=body)
        print(f"  ✅ Draft created for {first_name} ({email})")

    print(f"\n✅ {len(dealshare_recipients)} draft(s) created in Gmail.\n")
