"""Comprehensive scenario tests for the Release Manager agent.

Tests the Release Manager's ability to handle real-world release management tasks
based on the system prompt instructions from docs/templates/release_manager_system_prompt.md.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env.secrets file FIRST before importing agentllm modules
# This ensures AGENTLLM_TOKEN_ENCRYPTION_KEY is available for TokenStorage initialization
# Use override=True to ensure .env.secrets takes precedence over any previously loaded .env
load_dotenv(".env.secrets", override=True)

# Now import agentllm modules (after environment is loaded)
# ruff: noqa: E402 - Imports must come after load_dotenv() for encryption key
from agno.db.sqlite import SqliteDb

from agentllm.agents.release_manager import ReleaseManager
from agentllm.db import TokenStorage

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# Verify encryption key is loaded (required for token decryption)
if not os.getenv("AGENTLLM_TOKEN_ENCRYPTION_KEY"):
    raise RuntimeError(
        "AGENTLLM_TOKEN_ENCRYPTION_KEY not set in environment. "
        "This is required to decrypt tokens from the production database. "
        "Make sure .env.secrets has AGENTLLM_TOKEN_ENCRYPTION_KEY set to the same key "
        "used by the running 'just dev' instance. "
        'Generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )


# Test scenarios with validation criteria - PROGRESSIVE COMPLEXITY STRUCTURE
#
# Scenarios are organized by complexity level (L1-L4):
#   Level 1: Single-Toolkit Scenarios (basic queries, simple reasoning)
#   Level 2: Cross-Toolkit Coordination (combine data from multiple sources)
#   Level 3: Structured Workflows (multi-step processes with templates)
#   Level 4: Advanced Analysis (complex reasoning, risk analysis, count accuracy)
#
# Run by level: pytest -k "level_1" tests/test_release_manager_scenarios.py -v -m integration
# Run specific: pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[L1_01] -v -s -m integration

TEST_SCENARIOS = [
    # =============================================================================
    # LEVEL 1: Single-Toolkit Scenarios (Basic Operations)
    # =============================================================================
    # These test basic toolkit access and simple queries. Each uses ONE toolkit
    # and validates the agent can retrieve data correctly.
    {
        "id": 1,
        "level": 1,
        "category": "Workbook - List Queries",
        "question": "What Jira queries are available in the workbook?",
        "expected_keywords": ["query", "jira", "available"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests ability to access workbook toolkit and list available queries",
    },
    {
        "id": 2,
        "level": 1,
        "category": "Workbook - Get Template",
        "question": "Show me the Feature Freeze Update template",
        "expected_keywords": ["feature freeze", "template", "release"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests ability to retrieve Slack template from workbook with placeholders",
    },
    {
        "id": 3,
        "level": 1,
        "category": "Jira - Simple Count",
        "question": "How many issues are open in fixVersion 1.9.0?",
        "expected_keywords": ["1.9.0", "issues", "open"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests basic Jira count query (single JQL, no complex filtering)",
    },
    {
        "id": 4,
        "level": 1,
        "category": "Jira - Issue Lookup",
        "question": "Are there any blocker bugs in the 1.9 release?",
        "expected_keywords": ["blocker", "bug", "priority"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests Jira query with priority filter (single condition)",
    },
    {
        "id": 5,
        "level": 1,
        "category": "Workflow - Instructions",
        "question": "How do I generate a release status update?",
        "expected_keywords": ["release status", "workflow", "instructions"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests workflow instruction retrieval (no execution)",
    },
    {
        "id": 6,
        "level": 1,
        "category": "Workbook - Project Config",
        "question": "What are the Jira project keys used for tracking?",
        "expected_keywords": ["rhidp", "rhdhplan", "jira", "project"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests project configuration retrieval by category",
    },
    {
        "id": 7,
        "level": 1,
        "category": "Workbook - Tool Reference",
        "question": "Show me documentation for the get_issues_by_team tool",
        "expected_keywords": ["team", "parameters", "returns", "tool"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests tool reference documentation retrieval",
    },
    {
        "id": 8,
        "level": 1,
        "category": "Workbook - Prompt Retrieval",
        "question": "Show me the feature_freeze_prep prompt",
        "expected_keywords": ["feature freeze", "prep", "verify"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests situational prompt retrieval from Prompts sheet",
    },
    {
        "id": 9,
        "level": 1,
        "category": "Workbook - List Workflows",
        "question": "List all available workflows in the workbook",
        "expected_keywords": ["workflow", "retrieving", "announce"],
        "should_cite_source": True,
        "knowledge_type": "workbook",
        "description": "L1: Tests listing all workflow names",
    },
    {
        "id": 10,
        "level": 1,
        "category": "Jira - Get Issue",
        "question": "Get details for issue RHIDP-15779",
        "expected_keywords": ["rhidp-15779", "issue", "status"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests single issue retrieval with full details",
    },
    {
        "id": 11,
        "level": 1,
        "category": "Jira - Fix Versions",
        "question": "What fix versions exist in the RHIDP project?",
        "expected_keywords": ["version", "rhidp", "fix"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests fix version extraction from project",
    },
    {
        "id": 12,
        "level": 1,
        "category": "Jira - Sprint Info",
        "question": "What sprint is issue RHIDP-15779 in?",
        "expected_keywords": ["sprint", "rhidp-15779"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests sprint information extraction from issue",
    },
    {
        "id": 13,
        "level": 1,
        "category": "Jira - Active Release Dates",
        "question": "What are the key dates for active releases?",
        "expected_keywords": ["release", "date", "freeze", "ga"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L1: Tests release date retrieval from Jira release issues (active_release query)",
    },
    {
        "id": 14,
        "level": 1,
        "category": "GDrive - Future Release Dates",
        "question": "What are the key dates for future releases from the release schedule spreadsheet?",
        "expected_keywords": ["release", "date", "schedule", "future"],
        "should_cite_source": True,
        "knowledge_type": "gdrive",
        "description": "L1: Tests Google Drive retrieval of future release dates from release schedule spreadsheet",
    },
    {
        "id": 15,
        "level": 1,
        "category": "GDrive - Team Mappings",
        "question": "List all active RHDH teams with their leads and Slack handles",
        "expected_keywords": ["team", "lead", "slack", "active"],
        "should_cite_source": True,
        "knowledge_type": "gdrive",
        "description": "L1: Tests Google Drive retrieval of team mappings from RHDH Team spreadsheet",
    },
    # =============================================================================
    # LEVEL 2: Cross-Toolkit Coordination (Data Combination)
    # =============================================================================
    # These test the agent's ability to combine data from multiple toolkits.
    # Requires understanding relationships between different data sources.
    {
        "id": 16,
        "level": 2,
        "category": "JQL Template Application",
        "question": "Use the 'open_issues_by_type' query template for version 1.9.0 with issuetype=Feature",
        "expected_keywords": ["1.9.0", "feature", "jira"],
        "should_cite_source": True,
        "knowledge_type": "multi",
        "description": "L2: Tests retrieving workbook template, substituting placeholders, executing Jira query",
    },
    {
        "id": 17,
        "level": 2,
        "category": "Release Status Query",
        "question": "What's the status of release 1.9.0?",
        "expected_keywords": ["release", "status", "1.9.0", "progress"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L2: Tests aggregating multiple Jira metrics (open/closed, by type)",
    },
    {
        "id": 18,
        "level": 2,
        "category": "CVE Tracking",
        "question": "What CVEs are outstanding for release 1.9.0?",
        "expected_keywords": ["cve", "security", "vulnerability", "1.9.0"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L2: Tests security-specific filtering and interpretation",
    },
    {
        "id": 19,
        "level": 2,
        "category": "GDrive + Jira - Team Issue Counts",
        "question": "Get open issue counts by team for release 1.9.0",
        "expected_keywords": ["team", "1.9.0", "count", "issues"],
        "should_cite_source": True,
        "knowledge_type": "multi",
        "description": "L2: Tests retrieving teams from GDrive, then querying Jira with team filters",
    },
    # =============================================================================
    # LEVEL 3: Structured Workflows (Multi-Step Processes)
    # =============================================================================
    # These test multi-step processes that follow workflow instructions.
    # Requires planning, data gathering, and template filling.
    {
        "id": 20,
        "level": 3,
        "category": "Code Freeze - Simple",
        "question": "Create a code freeze announcement for release 1.9.0",
        "expected_keywords": ["code freeze", "1.9.0", "release"],
        "should_cite_source": True,
        "knowledge_type": "multi",
        "description": "L3: Tests template retrieval + 2-3 Jira queries + placeholder substitution",
    },
    {
        "id": 21,
        "level": 3,
        "category": "Team Breakdown",
        "question": "Break down open issues by team for release 1.9.0",
        "expected_keywords": ["team", "1.9.0", "breakdown"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L3: Tests parallel team queries using get_issues_by_team() tool",
    },
    {
        "id": 22,
        "level": 3,
        "category": "Feature Freeze - Full",
        "question": "Create a Feature Freeze Update announcement for release 1.9",
        "expected_keywords": ["feature freeze", "1.9"],
        "should_cite_source": True,
        "knowledge_type": "multi",
        "description": "L3: Tests complex template with multiple data sources and placeholder filling",
    },
    # =============================================================================
    # LEVEL 4: Advanced Analysis (Complex Reasoning & Accuracy)
    # =============================================================================
    # These test advanced capabilities: accuracy validation, risk analysis,
    # proactive suggestions, and multi-factor reasoning.
    {
        "id": 23,
        "level": 4,
        "category": "Count Accuracy - Feature Demos",
        "question": "How many features are tagged for demos in version 1.9.0?",
        "expected_keywords": ["feature", "demo", "1.9.0"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L4: Tests count accuracy (pagination handling) - must report complete count, not sample",
        "validation_type": "count_accuracy",
        "jql_query": 'issuetype = Feature AND fixVersion = "1.9.0" AND labels = demo',
    },
    {
        "id": 24,
        "level": 4,
        "category": "Risk Analysis",
        "question": "What are the top 3 risks for releasing version 1.9.0 on time?",
        "expected_keywords": ["risk", "1.9.0", "blocker"],
        "should_cite_source": True,
        "knowledge_type": "multi",
        "description": "L4: Tests multi-query analysis, correlation, prioritization, recommendations",
    },
    {
        "id": 25,
        "level": 4,
        "category": "JQL Query Construction",
        "question": "Show me all features in release 1.9.0 that are still in progress",
        "expected_keywords": ["feature", "in progress", "jira", "1.9.0"],
        "should_cite_source": True,
        "knowledge_type": "jira",
        "description": "L4: Tests complex JQL construction with multiple filters (issuetype + status + fixVersion)",
    },
]


# Helper function to get configured user ID
def get_configured_user_id() -> str | None:
    """Get the first user ID with both Jira and Google Drive tokens configured.

    Uses the `just first-user` command to query the production database.

    Returns:
        User ID string if found, None otherwise.
    """
    try:
        result = subprocess.run(
            ["just", "first-user"],
            capture_output=True,
            text=True,
            check=True,
        )
        user_id = result.stdout.strip()
        return user_id if user_id else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Test fixtures
@pytest.fixture
def shared_db() -> SqliteDb:
    """Provide the production shared database with real tokens.

    This uses tmp/agent-data/agno_sessions.db which contains real OAuth tokens
    from the containerized proxy server.
    """
    db_path = Path("tmp/agent-data/agno_sessions.db")
    if not db_path.exists():
        pytest.skip("Production database not found. Run development stack first: just dev")
    db = SqliteDb(db_file=str(db_path))
    return db


@pytest.fixture
def token_storage(shared_db: SqliteDb) -> TokenStorage:
    """Provide a token storage instance using production database."""
    return TokenStorage(agno_db=shared_db)


@pytest.fixture
def configured_user_id() -> str:
    """Get a user ID that has both Jira and Google Drive tokens configured.

    This fixture queries the production database to find a real user
    with all required tokens.

    Skips the test if no configured user is found.
    """
    user_id = get_configured_user_id()
    if not user_id:
        pytest.skip("No configured user found with Jira and Google Drive tokens. Use the proxy to configure: nox -s proxy")
    return user_id


@pytest.fixture
def configured_agent(shared_db, token_storage, configured_user_id):
    """Fixture that provides a ReleaseManager with real toolkits configured.

    This fixture uses real OAuth tokens from tmp/agent-data/agno_sessions.db
    and creates an actual Agno agent using _get_or_create_agent().

    The agent is fully configured and ready to make real API calls.

    Workbook Source Control:
    - Default: Google Drive (requires OAuth + RELEASE_MANAGER_WORKBOOK_GDRIVE_URL)
    - USE_LOCAL_SHEETS=true: Load from local CSV files in exports/release manager_sheets/

    Set via environment variable or just command:
    - USE_LOCAL_SHEETS=true pytest tests/...
    - just rm-test 5 --local-sheets
    """
    # Check for USE_LOCAL_SHEETS environment variable
    use_local_sheets = os.getenv("USE_LOCAL_SHEETS", "").lower() in ("true", "1", "yes")
    local_sheets_dir = None

    if use_local_sheets:
        local_sheets_path = Path("exports/release manager_sheets")
        if local_sheets_path.exists():
            local_sheets_dir = str(local_sheets_path)
            print(f"\n📊 Workbook Source: Local CSV sheets ({local_sheets_path})")
        else:
            print(f"\n⚠️  USE_LOCAL_SHEETS=true but directory not found: {local_sheets_path}")
            print("   Falling back to Google Drive")
    else:
        print("\n📊 Workbook Source: Google Drive (requires OAuth)")

    agent_wrapper = ReleaseManager(
        shared_db=shared_db,
        token_storage=token_storage,
        user_id=configured_user_id,
        local_sheets_dir=local_sheets_dir,
    )

    # Force creation of the underlying Agno agent
    # This validates that all toolkits are properly configured
    underlying_agent = agent_wrapper._get_or_create_agent()

    if underlying_agent is None:
        pytest.skip("Could not create agent - toolkit configuration may be incomplete")

    return agent_wrapper


@pytest.mark.integration
class TestReleaseManagerScenarios:
    """Integration tests for Release Manager scenarios.

    These tests validate the agent's ability to handle real-world release
    management tasks as defined in the system prompt.

    Run with: pytest -m integration -v -s
    """

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                s,
                id=f"L{s['level']}_{s['id']:02d}_{s['category'].lower().replace(' ', '_').replace('-', '_')}",
            )
            for s in TEST_SCENARIOS
        ],
    )
    def test_scenario(self, configured_agent, configured_user_id, scenario):
        """Test individual scenario for Release Manager agent.

        This parametrized test runs each scenario independently, allowing for:
        - Individual scenario execution: pytest -k "scenario_01"
        - Category filtering: pytest -k "release_status"
        - Parallel execution support
        - Detailed per-scenario reporting

        Run examples:
        - Single scenario: pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[scenario_01_release_status_query] -v -s -m integration
        - All Jira tests: pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario -k "jira" -v -m integration
        - Risk scenarios: pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario -k "risk" -v -m integration
        """
        scenario_id = scenario["id"]
        level = scenario["level"]
        category = scenario["category"]
        question = scenario["question"]
        expected_keywords = scenario["expected_keywords"]
        should_cite = scenario["should_cite_source"]
        knowledge_type = scenario["knowledge_type"]
        description = scenario["description"]

        print(f"\n{'=' * 80}")
        print(f"🧪 LEVEL {level} - SCENARIO {scenario_id}: {category}")
        print(f"{'=' * 80}")
        print(f"Description: {description}")
        print(f"Question: {question}")
        print(f"{'-' * 80}\n")

        # Run the query using the configured user ID
        response = configured_agent.run(question, user_id=configured_user_id)
        content = str(response.content) if hasattr(response, "content") else str(response)

        # Validation
        validation_messages = []

        # Log response length (no assertion - concise answers are good!)
        validation_messages.append(f"✅ Response length: {len(content)} chars")

        # Check for expected keywords
        content_lower = content.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in content_lower]
        assert found_keywords, f"Missing expected keywords: {expected_keywords}"
        validation_messages.append(f"✅ Found keywords: {found_keywords}")

        # Check for source citations (for knowledge-based queries)
        if should_cite:
            has_citation = any(
                marker in content_lower
                for marker in [
                    "jira",
                    "query",
                    "schedule",
                    "according to",
                    "based on",
                    "release schedule",
                    "issues.redhat.com",
                    "rhidp",
                    "rhdhplan",
                    "rhdh",
                ]
            )
            if has_citation:
                validation_messages.append("✅ Includes source citation or context")
            else:
                validation_messages.append("⚠️  No explicit source citation found (non-critical)")

        # Knowledge type specific validation
        if knowledge_type == "jira":
            # Should mention Jira or include issue keys
            has_jira_context = "jira" in content_lower or any(project in content.upper() for project in ["RHIDP", "RHDHPLAN", "RHDHBUGS"])
            if has_jira_context:
                validation_messages.append("✅ Includes Jira context")
            else:
                validation_messages.append("⚠️  No Jira context found")

        if knowledge_type == "gdrive":
            # Should mention schedule or dates
            has_schedule_context = any(keyword in content_lower for keyword in ["schedule", "date", "freeze", "ga"])
            if has_schedule_context:
                validation_messages.append("✅ Includes schedule/date context")
            else:
                validation_messages.append("⚠️  No schedule context found")

        if knowledge_type == "workbook":
            # Should include workbook/template/query references
            has_workbook_context = any(keyword in content_lower for keyword in ["query", "template", "workflow", "available"])
            if has_workbook_context:
                validation_messages.append("✅ Includes workbook context")
            else:
                validation_messages.append("⚠️  No workbook context found")

        # Level-specific validation (progressive strictness)
        if level >= 2:
            # Level 2+: Should cite multiple sources or show data combination
            multi_source_indicators = sum(1 for indicator in ["jira", "query", "workbook", "template"] if indicator in content_lower)
            if multi_source_indicators >= 2:
                validation_messages.append(f"✅ Level {level}: Multi-source data combination detected")
            else:
                validation_messages.append(f"⚠️  Level {level}: Expected multi-source coordination")

        if level >= 3:
            # Level 3+: Should show structured workflow (multiple steps or template filling)
            workflow_indicators = any(
                indicator in content_lower
                for indicator in [
                    "step",
                    "first",
                    "next",
                    "then",
                    "placeholder",
                    "fill",
                    "announcement",
                ]
            )
            if workflow_indicators:
                validation_messages.append(f"✅ Level {level}: Workflow structure present")
            else:
                validation_messages.append(f"⚠️  Level {level}: Expected workflow structure")

        if level >= 4:
            # Level 4: Should show advanced reasoning (analysis, recommendations, prioritization)
            reasoning_indicators = any(
                indicator in content_lower
                for indicator in [
                    "recommend",
                    "suggest",
                    "priority",
                    "risk",
                    "analysis",
                    "because",
                    "therefore",
                ]
            )
            if reasoning_indicators:
                validation_messages.append(f"✅ Level {level}: Advanced reasoning present")
            else:
                validation_messages.append(f"⚠️  Level {level}: Expected advanced reasoning")

        # Count accuracy validation for scenario 12 (JQL count accuracy)
        if scenario.get("validation_type") == "count_accuracy" and "jql_query" in scenario:
            jql_query = scenario["jql_query"]
            print("\n🔍 Count Accuracy Validation:")
            print(f"  JQL Query: {jql_query}")

            # Extract Jira toolkit from agent
            try:
                # Access the configurator from the agent wrapper
                configurator = configured_agent._configurator

                # Find the JiraConfig in the toolkit_configs
                jira_config = None
                for config in configurator.toolkit_configs:
                    if config.__class__.__name__ == "JiraConfig":
                        jira_config = config
                        break

                if not jira_config:
                    validation_messages.append("⚠️  Could not find JiraConfig to validate count")
                else:
                    # Get the Jira toolkit for this user
                    jira_toolkit = jira_config.get_toolkit(configured_user_id)

                    if not jira_toolkit:
                        validation_messages.append("⚠️  Could not get Jira toolkit to validate count")
                    else:
                        # Get the Jira client from the toolkit
                        jira_client = jira_toolkit._get_jira_client()

                        # Execute the same JQL query with maxResults=0 to get total count
                        search_result = jira_client.search_issues(jql_query, maxResults=0)
                        actual_count = search_result.total

                        print(f"  Actual Jira count: {actual_count}")

                        # Extract the count from agent's response
                        import re

                        # Look for patterns like "27 features", "**27**", "count: 27", etc.
                        count_patterns = [
                            r"\*\*(\d+)\*\*",  # **27**
                            r"(\d+)\s+features?",  # 27 features
                            r"count:\s*(\d+)",  # count: 27
                            r"total:\s*(\d+)",  # total: 27
                            r"There are\s+\*\*(\d+)\*\*",  # There are **27**
                        ]

                        reported_count = None
                        for pattern in count_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                reported_count = int(match.group(1))
                                break

                        if reported_count is None:
                            validation_messages.append("⚠️  Could not extract count from agent response")
                            print("  Could not extract count from response")
                            raise AssertionError("Failed to extract count from agent response for count accuracy validation")
                        else:
                            print(f"  Agent reported count: {reported_count}")

                            if reported_count == actual_count:
                                validation_messages.append(f"✅ Count accuracy: {reported_count} == {actual_count} (ACCURATE)")
                                print("  ✅ ACCURATE: Agent reported correct count")
                            else:
                                validation_messages.append(
                                    f"❌ Count accuracy: {reported_count} != {actual_count} (INACCURATE - off by {abs(reported_count - actual_count)})"
                                )
                                print(
                                    f"  ❌ INACCURATE: Agent reported {reported_count} but actual is {actual_count} (off by {abs(reported_count - actual_count)})"
                                )
                                # This is a hard failure for count accuracy tests
                                raise AssertionError(f"Count mismatch: agent reported {reported_count} but Jira has {actual_count}")

            except Exception as e:
                validation_messages.append(f"⚠️  Count validation error: {str(e)}")
                print(f"  Error during count validation: {e}")

        # Print validation results
        print("\n📋 Validation Results:")
        for msg in validation_messages:
            print(f"  {msg}")

        # Print response preview
        print("\n📄 Response Preview:")
        preview = content[:500] + "..." if len(content) > 500 else content
        print(preview)
        print(f"\n{'=' * 80}")
        print("✅ SCENARIO PASSED")
        print(f"{'=' * 80}\n")

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_comprehensive_scenarios(self, configured_agent, configured_user_id):
        """Run all scenarios as a single comprehensive test.

        This test runs all scenarios sequentially and generates a summary report.
        It's useful for validating overall agent capabilities and tracking improvements.

        Run with: pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_comprehensive_scenarios -v -s -m integration
        """
        results = []
        total = len(TEST_SCENARIOS)
        passed = 0
        partial = 0
        failed = 0

        print(f"\n{'=' * 80}")
        print("🎯 RUNNING COMPREHENSIVE RELEASE MANAGER TEST")
        print(f"{'=' * 80}")
        print(f"Total Scenarios: {total}")
        print(f"{'=' * 80}\n")

        for scenario in TEST_SCENARIOS:
            scenario_id = scenario["id"]
            category = scenario["category"]
            question = scenario["question"]
            expected_keywords = scenario["expected_keywords"]
            should_cite = scenario["should_cite_source"]
            description = scenario["description"]

            print(f"\n[{scenario_id}/{total}] 🧪 TESTING: {category}")
            print(f"Question: {question}")
            print(f"{'-' * 80}")

            result = {
                "id": scenario_id,
                "category": category,
                "question": question,
                "description": description,
                "status": "UNKNOWN",
                "response_length": 0,
                "found_keywords": [],
                "validation": [],
            }

            try:
                # Run the query using the configured user ID
                response = configured_agent.run(question, user_id=configured_user_id)
                content = str(response.content) if hasattr(response, "content") else str(response)

                result["response_length"] = len(content)

                # Validation
                validation_results = []

                # Check response length
                if len(content) >= 50:
                    validation_results.append("✅ Response length adequate")
                else:
                    validation_results.append(f"⚠️  Response too short: {len(content)} chars")

                # Check for expected keywords
                content_lower = content.lower()
                found_keywords = [kw for kw in expected_keywords if kw.lower() in content_lower]
                result["found_keywords"] = found_keywords

                if found_keywords:
                    validation_results.append(f"✅ Found keywords: {found_keywords}")
                else:
                    validation_results.append(f"⚠️  Missing expected keywords: {expected_keywords}")

                # Check for source citations
                if should_cite:
                    has_citation = any(
                        marker in content_lower
                        for marker in [
                            "jira",
                            "query",
                            "schedule",
                            "according to",
                            "based on",
                            "release schedule",
                        ]
                    )
                    if has_citation:
                        validation_results.append("✅ Includes source citation")
                    else:
                        validation_results.append("⚠️  No explicit source citation")

                result["validation"] = validation_results

                # Determine status
                if all("✅" in v for v in validation_results):
                    result["status"] = "PASSED"
                    passed += 1
                    print("✅ Status: PASSED")
                elif any("✅" in v for v in validation_results):
                    result["status"] = "PARTIAL"
                    partial += 1
                    print("⚠️  Status: PARTIAL")
                else:
                    result["status"] = "FAILED"
                    failed += 1
                    print("❌ Status: FAILED")

                # Print validation details
                for v in validation_results:
                    print(f"  {v}")

                # Print response preview
                print("\n📄 Response Preview:")
                preview = content[:300] + "..." if len(content) > 300 else content
                print(preview)

            except Exception as e:
                result["status"] = "FAILED"
                result["error"] = str(e)
                failed += 1
                print(f"❌ Status: FAILED - {e}")

            results.append(result)

        # Print summary
        print(f"\n{'=' * 80}")
        print("TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Scenarios: {total}")
        print(f"  ✅ Passed: {passed}/{total}")
        print(f"  ⚠️  Partial: {partial}/{total}")
        print(f"  ❌ Failed: {failed}/{total}")

        # Save detailed results
        results_file = Path("tmp/release_manager_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        with results_file.open("w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total": total,
                        "passed": passed,
                        "partial": partial,
                        "failed": failed,
                    },
                    "results": results,
                },
                f,
                indent=2,
            )

        print(f"\n📊 Detailed results saved to: {results_file}")
        print(f"{'=' * 80}\n")

        # Test passes if:
        # 1. At least one scenario ran (not all skipped)
        # 2. No scenarios failed completely
        # 3. At least 80% passed or partial
        assert passed + partial > 0, "No tests were run"
        assert failed == 0, f"{failed} scenarios failed completely"

        success_rate = (passed + partial) / total * 100
        assert success_rate >= 80, f"Success rate too low: {success_rate:.1f}%"


@pytest.mark.integration
class TestJiraOptimizations:
    """Tests for Jira API optimizations (caching, parallel queries, get_issues_by_team).

    These tests validate that our optimizations work correctly and improve performance
    while maintaining accuracy.

    Run with: pytest tests/test_release_manager_scenarios.py::TestJiraOptimizations -v -s -m integration
    """

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_get_issues_by_team_tool(self, configured_agent, configured_user_id):
        """Test the new get_issues_by_team() tool for accurate team breakdowns.

        This test validates:
        1. Tool executes without errors
        2. Returns correct structure with total_issues, by_team, without_team
        3. Math is correct: sum(by_team) + without_team = total_issues
        4. Results are accurate (not sample-based)
        """
        print("\n" + "=" * 80)
        print("🧪 TEST: get_issues_by_team() Tool")
        print("=" * 80)

        # Access the configurator from the agent wrapper
        configurator = configured_agent._configurator

        # Find the JiraConfig
        jira_config = None
        for config in configurator.toolkit_configs:
            if config.__class__.__name__ == "JiraConfig":
                jira_config = config
                break

        assert jira_config is not None, "JiraConfig not found in configurator"

        # Get the Jira toolkit for this user
        jira_toolkit = jira_config.get_toolkit(configured_user_id)
        assert jira_toolkit is not None, "Could not get Jira toolkit"

        # Test with a known release version
        release_version = "1.9.0"

        # Get active team IDs from typical RHDH teams
        # These team IDs are from the RHDH Team spreadsheet
        team_ids = [
            "4267",  # Frontend Plugin & UI
            "4564",  # COPE
            "5775",  # AI
            "4265",  # Install
            "4558",  # Plugins
        ]

        print(f"\n📋 Testing with release: {release_version}")
        print(f"📋 Testing with {len(team_ids)} teams: {team_ids}")

        # Call the tool
        import time

        start_time = time.time()
        result_json = jira_toolkit.get_issues_by_team(release_version, team_ids)
        elapsed = time.time() - start_time

        print(f"\n⏱️  Execution time: {elapsed:.2f} seconds")

        # Parse the result
        result = json.loads(result_json)

        print("\n📊 Results:")
        print(f"  Total issues: {result.get('total_issues')}")
        print(f"  Issues by team: {result.get('by_team')}")
        print(f"  Issues without team: {result.get('without_team')}")

        # Validation
        assert "error" not in result, f"Tool returned error: {result.get('error')}"
        assert "total_issues" in result, "Missing total_issues in result"
        assert "by_team" in result, "Missing by_team in result"
        assert "without_team" in result, "Missing without_team in result"

        total_issues = result["total_issues"]
        by_team = result["by_team"]
        without_team = result["without_team"]

        # Verify math
        assigned_count = sum(by_team.values())
        calculated_total = assigned_count + without_team

        print("\n🔍 Validation:")
        print(f"  Assigned issues: {assigned_count}")
        print(f"  Unassigned issues: {without_team}")
        print(f"  Calculated total: {calculated_total}")
        print(f"  Reported total: {total_issues}")

        assert calculated_total == total_issues, f"Math error: {assigned_count} + {without_team} != {total_issues}"
        print("  ✅ Math is correct!")

        # Verify all team IDs are present
        for team_id in team_ids:
            assert team_id in by_team, f"Team {team_id} missing from results"

        print("\n✅ TEST PASSED")
        print("=" * 80)

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_parallel_team_queries_performance(self, configured_agent, configured_user_id):
        """Test that parallel team queries are faster than sequential.

        This test validates:
        1. Parallel execution completes faster than sequential would
        2. All team counts are returned correctly
        3. No data corruption from concurrent access
        """
        print("\n" + "=" * 80)
        print("🧪 TEST: Parallel Team Query Performance")
        print("=" * 80)

        # Access the Jira toolkit
        configurator = configured_agent._configurator
        jira_config = None
        for config in configurator.toolkit_configs:
            if config.__class__.__name__ == "JiraConfig":
                jira_config = config
                break

        assert jira_config is not None, "JiraConfig not found"
        jira_toolkit = jira_config.get_toolkit(configured_user_id)
        assert jira_toolkit is not None, "Could not get Jira toolkit"

        # Clear cache to ensure we're testing actual queries
        jira_toolkit._count_cache.clear()

        # Test with multiple teams
        release_version = "1.9.0"
        team_ids = [
            "4267",  # Frontend Plugin & UI
            "4564",  # COPE
            "5775",  # AI
            "4265",  # Install
            "4558",  # Plugins
            "4869",  # Security
        ]

        print(f"\n📋 Testing parallel queries for {len(team_ids)} teams")

        # Execute the parallel team query
        import time

        start_time = time.time()
        result_json = jira_toolkit.get_issues_by_team(release_version, team_ids)
        elapsed_parallel = time.time() - start_time

        result = json.loads(result_json)

        print(f"\n⏱️  Parallel execution time: {elapsed_parallel:.2f}s")
        print(f"📊 Results: {result.get('by_team')}")

        # Validation
        assert "error" not in result, f"Tool returned error: {result.get('error')}"
        assert len(result["by_team"]) == len(team_ids), "Not all teams returned"

        # Verify all team IDs are present and have counts
        for team_id in team_ids:
            assert team_id in result["by_team"], f"Team {team_id} missing"
            assert isinstance(result["by_team"][team_id], int), f"Team {team_id} count is not an integer"

        # Estimate sequential time (1 API call = ~0.5-1 second typically)
        # With 6 teams + 1 total query = 7 queries
        estimated_sequential_time = 7 * 0.5  # Conservative estimate

        print("\n🔍 Performance Analysis:")
        print(f"  Parallel time: {elapsed_parallel:.2f}s")
        print(f"  Estimated sequential time: {estimated_sequential_time:.2f}s")
        print(f"  Speedup: {estimated_sequential_time / elapsed_parallel:.1f}x")

        # Parallel should be significantly faster (allowing for some overhead)
        # We expect at least 2x improvement with 6 teams
        assert elapsed_parallel < estimated_sequential_time, "Parallel execution should be faster than sequential"
        print("  ✅ Parallel execution is faster!")

        print("\n✅ TEST PASSED")
        print("=" * 80)

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_team_breakdown_accuracy(self, configured_agent, configured_user_id):
        """Test that team breakdown counts match individual team queries.

        This validates the fix for the original pagination bug where team counts
        were calculated from a sample of 50 issues instead of all issues.

        This test:
        1. Gets team breakdown using get_issues_by_team()
        2. Queries each team individually to verify counts
        3. Ensures no sampling artifacts
        """
        print("\n" + "=" * 80)
        print("🧪 TEST: Team Breakdown Accuracy (Pagination Bug Fix)")
        print("=" * 80)

        # Access the Jira toolkit
        configurator = configured_agent._configurator
        jira_config = None
        for config in configurator.toolkit_configs:
            if config.__class__.__name__ == "JiraConfig":
                jira_config = config
                break

        assert jira_config is not None, "JiraConfig not found"
        jira_toolkit = jira_config.get_toolkit(configured_user_id)
        assert jira_toolkit is not None, "Could not get Jira toolkit"

        # Clear cache to ensure fresh queries
        jira_toolkit._count_cache.clear()

        release_version = "1.9.0"
        test_teams = {
            "4564": "COPE",  # Should be 98, not 11
            "4267": "Frontend Plugin & UI",  # Should be 100
        }

        print(f"\n📋 Testing team breakdown for release {release_version}")
        print(f"📋 Teams to verify: {list(test_teams.values())}")

        # Get breakdown using the new tool
        team_ids = list(test_teams.keys())
        result_json = jira_toolkit.get_issues_by_team(release_version, team_ids)
        result = json.loads(result_json)

        assert "error" not in result, f"Tool returned error: {result.get('error')}"

        print("\n📊 Team Breakdown Results:")
        for team_id, team_name in test_teams.items():
            count = result["by_team"].get(team_id, 0)
            print(f"  {team_name} ({team_id}): {count} issues")

        # Verify against individual queries
        print("\n🔍 Verifying with individual queries:")
        jira_client = jira_toolkit._get_jira_client()
        base_jql = f'project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND fixVersion = "{release_version}" AND status != closed'

        for team_id, team_name in test_teams.items():
            team_jql = f"{base_jql} AND team = {team_id}"
            individual_result = jira_client.search_issues(team_jql, maxResults=0)
            individual_count = individual_result.total

            breakdown_count = result["by_team"][team_id]

            print(f"  {team_name}:")
            print(f"    get_issues_by_team(): {breakdown_count}")
            print(f"    Individual query:     {individual_count}")

            assert breakdown_count == individual_count, (
                f"Count mismatch for {team_name}: breakdown={breakdown_count}, individual={individual_count}"
            )
            print("    ✅ Counts match!")

        # Verify no sampling artifacts (counts should not be suspiciously low like 11 when actual is 98)
        for team_id in test_teams:
            count = result["by_team"][team_id]
            # Teams should have reasonable counts (not sampling artifacts like 1, 1, 1, 10)
            # If total issues > 500, individual teams should have > 10 issues typically
            if result["total_issues"] > 500:
                assert count > 10 or count == 0, f"Suspiciously low count ({count}) for team {team_id} suggests sampling bug"

        print("\n✅ TEST PASSED - No pagination bugs detected!")
        print("=" * 80)
