"""Root conftest.py for AgentLLM tests.

This module provides pytest configuration and fixtures that are available
to all test modules.
"""

import os

import pytest


def pytest_configure(config):
    """Pytest configuration hook called before test collection.

    Automatically sets AGNO_DEBUG=true when running tests in verbose mode (-v).
    This provides detailed logging from Agno agents during test execution.

    Also sets up encryption key for token storage tests.

    Args:
        config: pytest Config object
    """
    # Set up encryption key for tests if not already set
    if "AGENTLLM_TOKEN_ENCRYPTION_KEY" not in os.environ:
        # Generate a test encryption key
        from cryptography.fernet import Fernet

        test_key = Fernet.generate_key().decode()
        os.environ["AGENTLLM_TOKEN_ENCRYPTION_KEY"] = test_key

    # Set up OAuth state secret for tests if not already set
    if "AGENTLLM_OAUTH_STATE_SECRET" not in os.environ:
        # Use a consistent test secret (not random) for predictable test behavior
        os.environ["AGENTLLM_OAUTH_STATE_SECRET"] = "test_oauth_state_secret_12345678901234567890123456789012"

    # Discover and register all toolkit token types
    # This imports all toolkit configs which auto-register their token models
    from agentllm.agents.toolkit_configs import discover_and_register_toolkits  # noqa: E402

    discover_and_register_toolkits()

    # Check if verbose mode is enabled (-v or -vv)
    verbose = config.getoption("verbose", 0)

    if verbose > 0:
        # Set AGNO_DEBUG for detailed Agno logging
        os.environ["AGNO_DEBUG"] = "true"

        # Also set show_tool_calls for better debugging
        if "AGNO_SHOW_TOOL_CALLS" not in os.environ:
            os.environ["AGNO_SHOW_TOOL_CALLS"] = "true"


def pytest_report_header(config):
    """Add custom header information to pytest output.

    Args:
        config: pytest Config object

    Returns:
        List of header lines to display
    """
    verbose = config.getoption("verbose", 0)
    headers = []

    if verbose > 0:
        headers.append(f"AGNO_DEBUG: {os.environ.get('AGNO_DEBUG', 'false')}")
        headers.append(f"AGNO_SHOW_TOOL_CALLS: {os.environ.get('AGNO_SHOW_TOOL_CALLS', 'false')}")

    return headers


@pytest.fixture
def mock_gdrive_workbook():
    """Mock Release Manager workbook data with all 7 sheets.

    Returns:
        Dictionary mapping sheet names to list of row dicts with proper column naming:
        - Machine-readable sheets (Configuration & Setup, Jira Queries,
          Actions & Workflows, Slack Templates, Prompts): lowercase_snake_case headers
        - Informational sheets (Tools Reference, Maintenance Guide): Title Case headers
    """
    return {
        "Configuration & Setup": [  # NOTE: snake_case columns (changed from Title Case)
            {
                "config_key": "jira_default_base_jql",
                "value": "project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND status != closed",
                "description": "Default JQL scope applied to Release Manager queries",
            },
            {
                "config_key": "team_mapping_gdrive_id",
                "value": "1Dv1JWsQe3Ew82WLFQNhyAwqsn9oEkh2MjoKyHXPuJkk",
                "description": "Google Drive file ID for RHDH Team Mapping spreadsheet",
            },
        ],
        "Tools Reference": [
            {
                "Tool Name": "get_issues_detailed",
                "Category": "Jira",
                "Parameters": "jql_query, fields=[], max_results=50",
                "Returns": "List of issues with custom fields",
                "Use When": "Need detailed issue info with custom fields",
                "Example": "get_issues_detailed('project = RHIDP', ['summary', 'status'])",
            },
            {
                "Tool Name": "get_issues_summary",
                "Category": "Jira",
                "Parameters": "jql_query, max_results=50",
                "Returns": "Basic issue list (key, summary, status)",
                "Use When": "Need simple issue listing",
                "Example": "get_issues_summary('fixVersion = 1.9.0')",
            },
        ],
        # NOTE: "Response Formats" removed - replaced by "Prompts" sheet (see below)
        "Jira Queries": [  # snake_case columns
            {
                "name": "jira list of active release",
                "description": "Get all active releases",
                "jql_template": "project = RHDHPlan AND issuetype = Release AND status != Closed",
                "placeholders": "",
                "example": "Returns all open releases",
                "notes": "",
            },
            {
                "name": "jira list of open issues by type query template",
                "description": "Get open issues for a release filtered by type",
                "jql_template": "project IN (RHIDP, RHDHBugs) AND fixVersion = '{{RELEASE_VERSION}}' AND issuetype = {{ISSUE_TYPE}} AND status != Closed",
                "placeholders": "{{RELEASE_VERSION}}, {{ISSUE_TYPE}}",
                "example": "fixVersion = '1.9.0' AND issuetype = Bug",
                "notes": "Filter by specific issue type",
            },
            {
                "name": "jira list of blockers",
                "description": "Get all blocker priority issues",
                "jql_template": "project IN (RHIDP, RHDHBugs) AND priority = Blocker AND status != Closed",
                "placeholders": "",
                "example": "All open blockers",
                "notes": "Critical issues only",
            },
        ],
        "Actions & Workflows": [  # snake_case columns
            {
                "name": "generate release status",
                "description": "Create weekly release status update",
                "input_required": "Release version",
                "data_sources": "Jira issues, Release schedule",
                "tools": "get_issues_stats, get_issues_summary",
                "output_format": "Release Status Update",
                "instructions": "1. Query open issues\n2. Calculate metrics\n3. Identify risks\n4. Format output",
            },
            {
                "name": "prepare freeze announcement",
                "description": "Generate Slack announcement for freeze milestone",
                "input_required": "Release version, Freeze date, Milestone type",
                "data_sources": "Jira issues, Slack Templates sheet",
                "tools": "get_slack_template, get_issues_stats",
                "output_format": "Slack Markdown",
                "instructions": "1. Get template\n2. Query outstanding items\n3. Fill placeholders\n4. Return copy-paste ready",
            },
        ],
        "Slack Templates": [  # snake_case columns
            {
                "name": "Feature Freeze Update",
                "milestone": "Feature Freeze",
                "when_to_send": "Before Feature Freeze date",
                "data_requirements": "Feature Freeze date, Active teams, Outstanding Release Notes count",
                "template_content": ":warning: *RHDH {{RELEASE_VERSION}} Feature Freeze* :warning:\n\n"
                "Freeze Date: {{FEATURE_FREEZE_DATE}}\n\n"
                "Outstanding:\n"
                "- Release Notes: {{RELEASE_NOTES_COUNT}}\n\n"
                "Please complete all items before freeze date.",
            },
            {
                "name": "Code Freeze Announcement",
                "milestone": "Code Freeze",
                "when_to_send": "1 week before Code Freeze",
                "data_requirements": "Code Freeze date, Open bugs count, Open features count",
                "template_content": ":stop_sign: *RHDH {{RELEASE_VERSION}} Code Freeze* :stop_sign:\n\n"
                "Freeze Date: {{CODE_FREEZE_DATE}}\n\n"
                "Current Status:\n"
                "- Open Bugs: {{OPEN_BUGS_COUNT}}\n"
                "- Open Features: {{OPEN_FEATURES_COUNT}}",
            },
        ],
        "Maintenance Guide": [  # Title Case columns
            {
                "Category": "Best Practices",
                "Topic": "JQL Query Construction",
                "Guideline/Issue": "Complex queries may hit pagination limits",
                "Recommendation/Solution": "Use get_issues_stats() for counts, not get_issues_detailed()",
                "Example": "For team breakdowns, use get_issues_by_team()",
                "Reference": "AGENTS.md Jira Tool Usage section",
            },
            {
                "Category": "Troubleshooting",
                "Topic": "Missing Template Placeholders",
                "Guideline/Issue": "Slack templates fail when placeholders not filled",
                "Recommendation/Solution": "Always query required data before filling template",
                "Example": "Query release notes count before using Feature Freeze template",
                "Reference": "Slack Templates sheet data_requirements column",
            },
        ],
        "Prompts": [  # snake_case columns
            {
                "name": "system_prompt",
                "description": "Core system prompt for Release Manager agent",
                "prompt_type": "system",
                "context": "Always active - defines agent identity and core capabilities",
                "prompt_content": "You are the Release Manager for RHDH. Use tools efficiently and provide actionable insights.",
            },
            {
                "name": "feature_freeze_prep",
                "description": "Guidance for preparing Feature Freeze announcement",
                "prompt_type": "situational",
                "context": "Use when user asks to prepare for Feature Freeze",
                "prompt_content": "When preparing Feature Freeze: 1) Get freeze date, 2) Gather team counts, 3) Use Slack template.",
            },
            {
                "name": "code_freeze_prep",
                "description": "Guidance for preparing Code Freeze announcement",
                "prompt_type": "situational",
                "context": "Use when user asks to prepare for Code Freeze",
                "prompt_content": "When preparing Code Freeze: 1) Get date, 2) Check blockers, 3) Use template.",
            },
            {
                "name": "risk_identification",
                "description": "How to identify and communicate release risks",
                "prompt_type": "situational",
                "context": "Use when analyzing release health",
                "prompt_content": "Risk indicators: blocker bugs, high open counts, missing release notes.",
            },
        ],
    }
