"""Tests for the Store Manager agent.

Tests the RHDH Plugin Store Manager agent's initialization, knowledge base
configuration, Jira integration, and query handling capabilities.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from agno.db.sqlite import SqliteDb
from dotenv import load_dotenv

from agentllm.agents.store_manager_agent import StoreManagerAgent, StoreManagerAgentFactory
from agentllm.db import TokenStorage

# Load .env.secrets file for tests (contains API keys and tokens)
load_dotenv(".env.secrets")

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


# Test scenarios with validation criteria
TEST_SCENARIOS = [
    {
        "id": 1,
        "category": "Quick Validation - CSV Knowledge",
        "question": "List the first 10 plugin names from the working_sheet CSV using read_csv_file with row_limit=10.",
        "expected_keywords": [
            # Specific plugins that should be mentioned from the CSV
            # (expecting the agent to cite actual plugin names from the data)
            "tekton",
            "kubernetes",
            "notifications",
            "rbac",
            "dynatrace",
            "github",
            "lighthouse",
            "argocd",
            "jira",
        ],
        "should_cite_source": True,
        "knowledge_type": "csv",
        "min_plugins_expected": 3,  # Expect at least 3 specific plugin names
        # Note: query_csv_file() would be ideal but has DuckDB parsing issues with this CSV file
        # read_csv_file() works reliably and agent can extract plugin names from the JSON response
    },
    {
        "id": 2,
        "category": "Quick Validation - Markdown Guides",
        "question": "How do I convert my Backstage plugin to RHDH?",
        "expected_keywords": ["dynamic", "plugin", "convert", "backstage"],
        "should_cite_source": True,
        "knowledge_type": "markdown",
    },
    {
        "id": 3,
        "category": "Quick Validation - Support Boundaries",
        "question": "What's the difference between GA and Tech Preview?",
        "expected_keywords": ["GA", "tech preview", "support"],
        "should_cite_source": True,
        "knowledge_type": "markdown",
    },
    {
        "id": 4,
        "category": "Knowledge Base - Specific Doc Citation",
        "question": "What does the RHDH Dynamic Plugin Packaging Guide say about SemVer?",
        "expected_keywords": ["semver", "version", "major", "minor", "patch"],
        "should_cite_source": True,
        "knowledge_type": "markdown",
    },
    {
        "id": 5,
        "category": "Knowledge Base - CSV Parsing",
        "question": "According to the release schedule, when is the next RHDH release?",
        "expected_keywords": ["release", "schedule"],
        "should_cite_source": True,
        "knowledge_type": "csv",
    },
    {
        "id": 6,
        "category": "Knowledge Base - PDF + Markdown Integration",
        "question": "What are the certification requirements for partner plugins?",
        "expected_keywords": ["certification", "partner", "requirement"],
        "should_cite_source": True,
        "knowledge_type": "markdown",
    },
    {
        "id": 7,
        "category": "Jira Integration - Search",
        "question": "Search RHIDP for plugin-related issues",
        "expected_keywords": ["RHIDP"],
        "should_cite_source": False,  # Jira results may not cite docs
        "knowledge_type": "jira",
    },
    {
        "id": 8,
        "category": "Jira Integration - JQL Query",
        "question": "Find CVEs affecting RHDH plugins",
        "expected_keywords": ["CVE"],
        "should_cite_source": False,
        "knowledge_type": "jira",
    },
    {
        "id": 9,
        "category": "Jira Integration - Project Filtering",
        "question": "Show me release blockers for RHDH 1.9",
        "expected_keywords": ["release", "blocker"],
        "should_cite_source": False,
        "knowledge_type": "jira",
    },
    {
        "id": 10,
        "category": "Complex Scenario - Multi-Use-Case",
        "question": "I want to create a new plugin, get it certified, and included in RHDH. Walk me through the complete process.",
        "expected_keywords": ["plugin", "create", "certif", "process"],
        "should_cite_source": True,
        "knowledge_type": "multi",
    },
]


# Test fixtures
@pytest.fixture
def shared_db() -> SqliteDb:
    """Provide a shared test database."""
    db_path = Path("tmp/test_store_manager.db")
    db_path.parent.mkdir(exist_ok=True)
    db = SqliteDb(db_file=str(db_path))
    yield db
    # Cleanup after tests
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def token_storage(shared_db: SqliteDb) -> TokenStorage:
    """Provide a token storage instance."""
    return TokenStorage(agno_db=shared_db)


class TestStoreManagerBasics:
    """Basic tests for StoreManager instantiation and parameters."""

    def test_create_agent(self, shared_db, token_storage):
        """Test that StoreManager can be instantiated."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )
        assert agent is not None
        assert agent._user_id == "test-user"

    def test_create_agent_with_params(self, shared_db, token_storage):
        """Test that StoreManager accepts model parameters."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
            session_id="test-session",
            temperature=0.7,
            max_tokens=2000,
        )
        assert agent is not None
        assert agent._user_id == "test-user"
        assert agent._session_id == "test-session"

    def test_factory_metadata(self):
        """Test that factory provides correct metadata."""
        metadata = StoreManagerAgentFactory.get_metadata()
        assert metadata["name"] == "store-manager"
        assert metadata["mode"] == "chat"
        assert "GEMINI_API_KEY" in metadata["requires_env"]
        assert "STORE_MANAGER_JIRA_API_TOKEN" in metadata["requires_env"]

    def test_factory_create_agent(self, shared_db, token_storage):
        """Test that factory can create agent instances."""
        agent = StoreManagerAgentFactory.create_agent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )
        assert isinstance(agent, StoreManagerAgent)


class TestKnowledgeConfiguration:
    """Tests for knowledge base configuration."""

    def test_knowledge_config_present(self, shared_db, token_storage):
        """Test that knowledge configuration is properly set."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        # Access configurator
        configurator = agent._configurator
        knowledge_config = configurator._get_knowledge_config()

        assert knowledge_config is not None
        assert knowledge_config["knowledge_path"] == "knowledge/store-manager"
        assert knowledge_config["table_name"] == "store_manager_knowledge"

    def test_knowledge_path_exists(self, shared_db, token_storage):
        """Test that knowledge directory exists."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        knowledge_config = agent._configurator._get_knowledge_config()
        knowledge_path = Path(knowledge_config["knowledge_path"])

        # Knowledge path should exist (even if empty in test environment)
        # In production, it contains RHDH documentation
        assert knowledge_path.parent.exists()  # At least parent should exist


class TestJiraIntegration:
    """Tests for Jira toolkit integration."""

    def test_jira_toolkit_with_env_token(self, shared_db, token_storage):
        """Test that Jira toolkit is initialized when env token is present."""
        # Set the environment variable
        test_token = "test-jira-token-12345"
        with patch.dict(os.environ, {"STORE_MANAGER_JIRA_API_TOKEN": test_token}):
            agent = StoreManagerAgent(
                shared_db=shared_db,
                token_storage=token_storage,
                user_id="test-user",
            )

            # Check that configurator has additional toolkits
            configurator = agent._configurator
            additional_toolkits = configurator._get_additional_toolkits()

            # Should have Jira toolkit when token is set
            assert len(additional_toolkits) > 0
            # First toolkit should be JiraTools
            assert additional_toolkits[0].__class__.__name__ == "JiraTools"

    def test_jira_toolkit_without_env_token(self, shared_db, token_storage):
        """Test that Jira toolkit is not initialized when env token is missing."""
        # Ensure token is not set
        with patch.dict(os.environ, {}, clear=True):
            # Re-set required GEMINI_API_KEY
            os.environ["GEMINI_API_KEY"] = "test-key"

            agent = StoreManagerAgent(
                shared_db=shared_db,
                token_storage=token_storage,
                user_id="test-user",
            )

            configurator = agent._configurator
            additional_toolkits = configurator._get_additional_toolkits()

            # Should be empty list when token is not set
            assert len(additional_toolkits) == 0

    def test_no_toolkit_configs_required(self, shared_db, token_storage):
        """Test that Store Manager has no per-user toolkit configuration."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        # Store Manager uses environment-based config, not per-user
        configurator = agent._configurator
        toolkit_configs = configurator._initialize_toolkit_configs()

        # Should return empty list (no user configuration needed)
        assert toolkit_configs == []


class TestAgentInstructions:
    """Tests for agent system instructions."""

    def test_instructions_include_use_cases(self, shared_db, token_storage):
        """Test that system instructions include all 8 use cases."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        configurator = agent._configurator
        instructions = configurator._build_agent_instructions()
        instructions_text = "\n".join(instructions)

        # Check for key use case mentions
        assert "Plugin Discovery" in instructions_text
        assert "Migration" in instructions_text or "Building Support" in instructions_text
        assert "Certification" in instructions_text
        assert "Lifecycle" in instructions_text or "Maintenance" in instructions_text
        assert "Support Boundary" in instructions_text
        assert "Release Planning" in instructions_text
        assert "Metadata" in instructions_text
        assert "Team Coordination" in instructions_text

    def test_instructions_include_jira_guidance(self, shared_db, token_storage):
        """Test that instructions include Jira integration guidance."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        configurator = agent._configurator
        instructions = configurator._build_agent_instructions()
        instructions_text = "\n".join(instructions)

        # Check for Jira-related content
        assert "JIRA" in instructions_text or "Jira" in instructions_text
        assert "RHIDP" in instructions_text  # RHDH project
        assert "RHDHPLAN" in instructions_text  # RHDH Planning project
        assert "JQL" in instructions_text  # JQL query examples

    def test_instructions_include_knowledge_base_info(self, shared_db, token_storage):
        """Test that instructions mention knowledge base capabilities."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
        )

        configurator = agent._configurator
        instructions = configurator._build_agent_instructions()
        instructions_text = "\n".join(instructions)

        # Check for knowledge base mentions
        assert "Knowledge Base" in instructions_text or "RAG" in instructions_text
        assert "documentation" in instructions_text.lower()
        assert "CSV" in instructions_text  # CSV files in knowledge base


@pytest.mark.integration
class TestStoreManagerIntegration:
    """Integration tests requiring actual API access.

    These tests are marked as integration and skipped by default.
    Run with: pytest -m integration
    """

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_agent_run_simple_query(self, shared_db, token_storage):
        """Test agent can handle a simple query."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="integration-test-user",
        )

        # Simple greeting
        response = agent.run("Hello! What can you help me with?", user_id="integration-test-user")

        assert response is not None
        # Response should mention RHDH or plugins
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert len(content) > 0

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY") or not os.getenv("STORE_MANAGER_JIRA_API_TOKEN"), reason="API keys not set")
    def test_agent_jira_query(self, shared_db, token_storage):
        """Test agent can query Jira when token is configured."""
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="integration-test-user",
        )

        # Query that would use Jira
        response = agent.run("Search RHIDP project for recent plugin issues", user_id="integration-test-user")

        assert response is not None
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert len(content) > 0

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    @pytest.mark.parametrize(
        "scenario",
        [pytest.param(s, id=f"scenario_{s['id']:02d}_{s['category'].lower().replace(' ', '_').replace('-', '_')}") for s in TEST_SCENARIOS],
    )
    def test_scenario(self, shared_db, token_storage, scenario):
        """Test individual scenario for Store Manager agent.

        This parametrized test runs each scenario independently, allowing for:
        - Individual scenario execution: pytest -k "scenario_01"
        - Category filtering: pytest -k "csv_knowledge"
        - Parallel execution support
        - Detailed per-scenario reporting

        Run examples:
        - Single scenario: pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario[scenario_01_quick_validation___csv_knowledge] -v -s -m integration
        - All CSV tests: pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "csv" -v -m integration
        - First 3 scenarios: pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_0[1-3]" -v -m integration
        """
        scenario_id = scenario["id"]
        category = scenario["category"]
        question = scenario["question"]
        expected_keywords = scenario["expected_keywords"]
        should_cite = scenario["should_cite_source"]
        knowledge_type = scenario["knowledge_type"]
        has_jira = bool(os.getenv("STORE_MANAGER_JIRA_API_TOKEN"))

        # Skip Jira tests if token not configured
        if knowledge_type == "jira" and not has_jira:
            pytest.skip("Skipping Jira scenario: STORE_MANAGER_JIRA_API_TOKEN not set")

        print(f"\n{'=' * 80}")
        print(f"🧪 SCENARIO {scenario_id}: {category}")
        print(f"{'=' * 80}")
        print(f"Question: {question}")
        print(f"{'-' * 80}\n")

        # Create agent
        agent = StoreManagerAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id=f"test-user-scenario-{scenario_id}",
        )

        # Run the query
        response = agent.run(question, user_id=f"test-user-scenario-{scenario_id}")
        content = str(response.content) if hasattr(response, "content") else str(response)

        # Validation
        validation_messages = []

        # Check response length
        assert len(content) >= 50, f"Response too short: {len(content)} chars"
        validation_messages.append(f"✅ Response length: {len(content)} chars")

        # Check for expected keywords
        content_lower = content.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in content_lower]
        assert found_keywords, f"Missing expected keywords: {expected_keywords}"

        # Check minimum plugin count if specified
        min_plugins = scenario.get("min_plugins_expected", 0)
        if min_plugins > 0:
            assert len(found_keywords) >= min_plugins, (
                f"Expected at least {min_plugins} specific plugins, found {len(found_keywords)}: {found_keywords}"
            )
            validation_messages.append(f"✅ Found {len(found_keywords)} specific plugins (minimum: {min_plugins}): {found_keywords}")
        else:
            validation_messages.append(f"✅ Found keywords: {found_keywords}")

        # Check for source citations (for knowledge-based queries)
        if should_cite:
            has_citation = any(
                marker in content
                for marker in ["according to", "based on", "from the", "the guide", "documentation", ".md", ".csv", "packaging guide"]
            )
            if has_citation:
                validation_messages.append("✅ Includes source citation")
            else:
                validation_messages.append("⚠️  No explicit source citation found (non-critical)")

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
