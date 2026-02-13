#!/usr/bin/env python3
"""Send Slack notification with triage results.

This script reads results.json and sends a formatted Slack message.
Sensitive data (ticket titles, teams, components) never appears in workflow logs.

Usage:
    python scripts/send_slack_notification.py
"""

import json
import os
import sys

import requests
from loguru import logger

# Constants
JIRA_SERVER_URL = "https://issues.redhat.com"


def format_ticket_line(item: dict) -> str:
    """Format a single ticket line for Slack.

    Args:
        item: Ticket dictionary with 'ticket', 'title', optional 'team', 'components',
              'team_is_new', and 'new_components'

    Returns:
        Formatted line like: "<title>[hyperlink] → Team: Security | Component: RBAC, *Keycloak*"
        New assignments are bolded, existing ones are not.
    """
    ticket = item["ticket"]
    title = item.get("title", ticket)  # Fallback to ticket ID if no title
    ticket_url = f"{JIRA_SERVER_URL}/browse/{ticket}"

    # Build assignment details
    parts = []
    if "team" in item:
        team_name = item["team"]
        # Bold and italic if team is newly assigned
        if item.get("team_is_new", False):
            parts.append(f"Team: *_{team_name}_*")
        else:
            parts.append(f"Team: {team_name}")

    if "components" in item and item["components"]:
        # Get list of new components
        new_components = item.get("new_components", [])

        # Format each component: bold+italic if new, regular if existing
        formatted_components = []
        for comp in item["components"]:
            if comp in new_components:
                formatted_components.append(f"*_{comp}_*")
            else:
                formatted_components.append(comp)

        components_str = ", ".join(formatted_components)
        parts.append(f"Component: {components_str}")

    # Format as: <URL|Title> with details on new line
    if parts:
        details = " | ".join(parts)
        return f"<{ticket_url}|{title}>\n>{details}"
    else:
        # No team or component (shouldn't happen, but handle gracefully)
        return f"<{ticket_url}|{title}>"


def build_slack_message(results: dict, items_subset: list = None,
                        include_header: bool = True) -> dict:
    """Build Slack message payload from results.

    Args:
        results: Results dictionary from auto_triage.py
        items_subset: Subset of items to include (for splitting large messages)
        include_header: Whether to include header with summary stats

    Returns:
        Slack webhook payload dictionary
    """
    total_count = results.get("total", 0)
    is_dry_run = results.get("applied", 0) == 0 and results.get("auto_apply", 0) > 0

    # Determine mode-specific wording
    if is_dry_run:
        header = "Jira Auto-Triage Summary (Dry-Run)"
        success_count = results.get("auto_apply", 0)
        success_label = "Would Assign"
        items_label = "Would Assign"
        items_emoji = "🔍"
        items = items_subset if items_subset is not None else results.get("auto_apply_items", [])
    else:
        header = "Jira Auto-Triage Summary"
        success_count = results.get("applied", 0)
        success_label = "Successfully Assigned"
        items_label = "Assigned Issues"
        items_emoji = "✅"
        items = items_subset if items_subset is not None else results.get("applied_items", [])

    # Format ticket lines
    ticket_lines = [format_ticket_line(item) for item in items]
    if ticket_lines:
        tickets_text = "\n".join(ticket_lines)
    else:
        tickets_text = "None"

    # Build main message
    blocks = []

    # Add header with summary stats (first message only)
    if include_header:
        blocks.extend([
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"Total Processed: *{total_count}*"},
                    {"type": "mrkdwn", "text": f"{success_label}: *{success_count}*"},
                ],
            }
        ])

    # Add items section (only show label in first message)
    if include_header:
        text = f"{items_emoji} *{items_label}:*\n{tickets_text}"
    else:
        text = tickets_text

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text,
        },
    })

    # Add failed section (apply mode only, first message only)
    if not is_dry_run and include_header:
        failed_count = results.get("failed", 0)
        if failed_count > 0:
            failed_items = results.get("failed_items", [])
            failed_lines = [format_ticket_line(item) for item in failed_items]
            failed_text = "\n".join(failed_lines) if failed_lines else "None"

            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Failed to Update ({failed_count}):*\n{failed_text}",
                    },
                }
            )

    return {"blocks": blocks}


def send_slack_notification(webhook_url: str, results: dict) -> bool:
    """Send Slack notification, splitting into multiple messages of 10 tickets each.

    Args:
        webhook_url: Slack webhook URL
        results: Results dictionary from auto_triage.py

    Returns:
        True if successful, False otherwise
    """
    try:
        is_dry_run = results.get("applied", 0) == 0 and results.get("auto_apply", 0) > 0

        # Get items to send
        if is_dry_run:
            items = results.get("auto_apply_items", [])
        else:
            items = results.get("applied_items", [])

        # Split into chunks of 10 tickets each
        CHUNK_SIZE = 10
        chunks = [items[i:i + CHUNK_SIZE] for i in range(0, len(items), CHUNK_SIZE)]

        if not chunks:
            chunks = [[]]  # Empty list if no items

        # Send each chunk
        for i, chunk in enumerate(chunks):
            # First message includes header with summary stats
            # Subsequent messages are just ticket lists
            include_header = (i == 0)

            payload = build_slack_message(
                results,
                items_subset=chunk if chunk else None,
                include_header=include_header
            )

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            if len(chunks) > 1:
                logger.info(f"Sent message {i + 1}/{len(chunks)}")

        logger.info("Slack notification sent successfully")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


def main():
    """Main entry point."""
    # Load results.json
    try:
        with open("results.json") as f:
            results = json.load(f)
    except FileNotFoundError:
        logger.error("results.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results.json: {e}")
        sys.exit(1)

    # Get Slack webhook URL
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("SLACK_WEBHOOK_URL not set, skipping notification")
        sys.exit(0)

    # Skip notification if nothing was processed
    total_count = results.get("total", 0)
    if total_count == 0:
        logger.info("No tickets processed, skipping notification")
        sys.exit(0)

    # Send notification
    success = send_slack_notification(webhook_url, results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
