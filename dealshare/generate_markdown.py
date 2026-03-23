"""
generate_markdown.py
--------------------
Generates the dealshare markdown file from Attio calls and Airtable deals.
Saves locally and opens in editor for review.
"""

import os
import subprocess
from datetime import datetime, timezone


SECTIONS = ["Seed", "Series A++", "Uncategorized"]


def format_calls_section(calls: list[dict]) -> str:
    if not calls:
        return ""
    lines = ["**Folks we met:**\n"]
    for call in calls:
        source = call.get("source", "").strip()
        company = call.get("company_name", "").strip()
        description = call.get("description", "").strip()
        linkedin = call.get("team_linkedin", "").strip()
        raise_details = call.get("raise_details", "").strip()

        if source:
            lines.append(f"*{source}*")
        if company:
            lines.append(company)
        if description:
            lines.append(description)
        if linkedin:
            lines.append(linkedin)
        if raise_details:
            lines.append(raise_details)
        lines.append("")
    return "\n".join(lines)


def format_deals_section(grouped: dict) -> str:
    lines = ["**Deals we've heard about:**\n"]
    has_content = False
    for section in SECTIONS:
        deals = grouped.get(section, [])
        if not deals:
            continue
        has_content = True
        lines.append(section)
        for deal in deals:
            name = deal.get("Company Name", "").strip()
            summary = deal.get("Summary", "").strip()
            line = name
            if summary:
                line += f" - {summary}"
            lines.append(line)
        lines.append("")
    if not has_content:
        lines.append("No new deals this week.")
    return "\n".join(lines)


def generate(calls: list[dict], grouped: dict, week_label: str) -> str:
    parts = [f"# Dealshare – Week of {week_label}\n"]
    calls_section = format_calls_section(calls)
    if calls_section:
        parts.append(calls_section)
    parts.append(format_deals_section(grouped))
    return "\n".join(parts)


def run(calls: list[dict], grouped: dict) -> str:
    """
    Generates markdown, saves to local file, opens in editor.
    Returns the filepath of the (potentially edited) file.
    """
    today = datetime.now(timezone.utc)
    week_label = today.strftime("%b %d, %Y")
    filename = f"Dealshare – Week of {week_label}.md"
    filepath = os.path.join(os.getcwd(), filename)

    content = generate(calls, grouped, week_label)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"\n📝 File saved: {filepath}")
    print("Opening for editing — review and make any changes, then save and close.")

    editor = os.environ.get("EDITOR", "open")
    subprocess.run([editor, filepath])

    input("\nPress Enter when you are done editing...")

    with open(filepath, "r") as f:
        final_content = f.read()

    print("✅ Edits captured.")
    return filepath, final_content
