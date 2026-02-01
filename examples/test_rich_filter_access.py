#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "jira>=3.0.0",
#     "loguru>=0.7.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""Prototype to test if we can access Rich Filter data via standard Jira filter API.

This script attempts to:
1. Connect to Jira (issues.redhat.com)
2. Retrieve filter #5807 (the Rich Filter)
3. Print the filter name and JQL query
4. Optionally execute the JQL to see what issues it returns

Usage:
    # Set environment variables first:
    export JIRA_TOKEN="your_jira_token"
    export JIRA_USERNAME="your_username"  # Optional

    # Then run:
    uv run examples/test_rich_filter_access.py
    # OR
    python examples/test_rich_filter_access.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from jira import JIRA
from loguru import logger

# Load .env.secrets from project root
project_root = Path(__file__).parent.parent
env_secrets_path = project_root / ".env.secrets"
if env_secrets_path.exists():
    load_dotenv(env_secrets_path)
    logger.info(f"Loaded credentials from {env_secrets_path}")
else:
    logger.warning(f".env.secrets not found at {env_secrets_path}")

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_rich_filter_access(filter_id: str = "5807"):
    """Test accessing a Rich Filter via the standard Jira filter API.

    Args:
        filter_id: The Jira filter ID (default: "5807")
    """
    # Get credentials from environment (.env.secrets or manual export)
    jira_token = os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_TOKEN")
    jira_username = os.getenv("JIRA_USERNAME")
    server_url = os.getenv("JIRA_SERVER_URL", "https://issues.redhat.com")

    if not jira_token:
        logger.error("JIRA_API_TOKEN not found in .env.secrets or environment")
        logger.info("Please ensure .env.secrets exists with JIRA_API_TOKEN set")
        return

    logger.info(f"Connecting to Jira at {server_url}")
    logger.info(f"Using authentication: {'basic auth (username + token)' if jira_username else 'token auth'}")

    try:
        # Connect to Jira
        if jira_username:
            jira = JIRA(
                server=server_url,
                basic_auth=(jira_username, jira_token),
            )
        else:
            jira = JIRA(
                server=server_url,
                token_auth=jira_token,
            )

        logger.success("✓ Connected to Jira successfully")

        # Test: Get current user to verify connection
        user = jira.myself()
        logger.info(f"Authenticated as: {user.get('displayName', user.get('name', 'Unknown'))}")

        # First, list available filters to see what we can access
        logger.info("\nListing your available filters...")
        try:
            my_filters = jira.favourite_filters()
            logger.info(f"Found {len(my_filters)} favorite filters:")
            for filt in my_filters[:10]:  # Show first 10
                print(f"  - Filter #{filt.id}: {filt.name}")
        except Exception as e:
            logger.warning(f"Could not list favorite filters: {e}")

        # Main test: Retrieve filter #5807
        logger.info(f"\nAttempting to retrieve filter #{filter_id}...")
        filter_obj = jira.filter(filter_id)

        logger.success("✓ Filter retrieved successfully!")

        # Print filter details
        print("\n" + "=" * 60)
        print(f"FILTER #{filter_id} DETAILS")
        print("=" * 60)
        print(f"Name:        {filter_obj.name}")
        print(f"Description: {getattr(filter_obj, 'description', 'N/A')}")
        print(f"Owner:       {getattr(filter_obj, 'owner', 'N/A')}")
        print(f"Favorite:    {getattr(filter_obj, 'favourite', 'N/A')}")
        print(f"JQL Query:   {filter_obj.jql}")
        print("=" * 60)

        # Optional: Test executing the JQL (default: true when running from script)
        execute_jql = os.getenv("EXECUTE_JQL", "true").lower() == "true"

        if execute_jql:
            logger.info("\nExecuting JQL query (fetching first 5 issues)...")
            issues = jira.search_issues(filter_obj.jql, maxResults=5)

            print(f"\nFound {len(issues)} issues (showing first 5):")
            print("-" * 60)
            for issue in issues:
                print(f"  {issue.key}: {issue.fields.summary}")
                print(f"    Status: {issue.fields.status.name}")
            print("-" * 60)
        else:
            logger.info("\nTo execute the JQL query, set: export EXECUTE_JQL=true")

        # Check if there are any Rich Filter-specific fields
        logger.info("\nChecking for Rich Filter-specific attributes...")
        all_attrs = [attr for attr in dir(filter_obj) if not attr.startswith("_")]
        print(f"Available attributes: {', '.join(all_attrs)}")

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        logger.exception("Full traceback:")
        return


if __name__ == "__main__":
    # Allow overriding filter ID via command line
    filter_id = sys.argv[1] if len(sys.argv) > 1 else "5807"

    print("=" * 60)
    print("RICH FILTER ACCESS PROTOTYPE")
    print("=" * 60)
    print(f"Target filter ID: {filter_id}")
    print()

    test_rich_filter_access(filter_id)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ If filter details were printed above, the standard Jira filter")
    print("  API CAN access the underlying filter that Rich Filters wraps.")
    print()
    print("✗ However, Rich Filter-specific features (smart filters, custom")
    print("  views, queues) are NOT accessible via this API.")
    print("=" * 60)
