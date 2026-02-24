"""Tests for the ReleaseManager agent with composition-based toolkit configs.

Tests both the agent's sync and async methods, including streaming functionality,
and verifies that toolkit configuration is properly checked before agent initialization.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from agno.db.sqlite import SqliteDb
from dotenv import load_dotenv

from agentllm.agents.release_manager import ReleaseManager
from agentllm.agents.toolkit_configs import JiraConfig
from agentllm.agents.toolkit_configs.release_manager_toolkit_config import ReleaseManagerToolkitConfig
from agentllm.db import TokenStorage

# Load .env file for tests
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


# Test fixtures
@pytest.fixture
def shared_db() -> SqliteDb:
    """Provide a shared test database."""
    db_path = Path("tmp/test_release_manager.db")
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


def _get_toolkit_configs(agent):
    """Helper to access toolkit_configs via the configurator."""
    return agent._configurator.toolkit_configs


class TestReleaseManagerBasics:
    """Basic tests for ReleaseManager instantiation and parameters."""

    def test_create_agent(self, shared_db, token_storage):
        """Test that ReleaseManager can be instantiated."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        assert agent is not None
        assert len(_get_toolkit_configs(agent)) > 0

    def test_create_agent_with_params(self, shared_db, token_storage):
        """Test that ReleaseManager accepts model parameters."""
        agent = ReleaseManager(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test-user",
            temperature=0.5,
            max_tokens=100,
        )
        assert agent is not None
        assert agent._configurator._temperature == 0.5
        assert agent._configurator._max_tokens == 100

    def test_toolkit_configs_initialized(self, shared_db, token_storage):
        """Test that toolkit configs are properly initialized."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        configs = _get_toolkit_configs(agent)
        assert isinstance(configs, list)
        # Should have JiraConfig and ReleaseManagerToolkitConfig
        assert len(configs) == 2

    def test_toolkit_config_types(self, shared_db, token_storage):
        """Test that toolkit configs have the expected types."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        config_types = [type(c).__name__ for c in _get_toolkit_configs(agent)]
        assert "JiraConfig" in config_types
        assert "ReleaseManagerToolkitConfig" in config_types


class TestToolkitConfiguration:
    """Tests for toolkit configuration management."""

    def test_required_toolkit_prompts_immediately(self, shared_db, token_storage):
        """Test that required toolkits prompt for config before agent can be used."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        configs = _get_toolkit_configs(agent)

        # Mock ReleaseManagerToolkitConfig as configured
        rm_config = next(c for c in configs if isinstance(c, ReleaseManagerToolkitConfig))
        with patch.object(rm_config, "is_configured", return_value=True):
            # Add a required toolkit config (mock JiraConfig as required)
            with patch.object(JiraConfig, "is_required", return_value=True):
                with patch.object(JiraConfig, "is_configured", return_value=False):
                    with patch.object(JiraConfig, "get_config_prompt", return_value="Please configure JIRA"):
                        # Add the mocked required config
                        configs.append(JiraConfig())

                        # User tries to send a message without configuring
                        response = agent.run("Hello!", user_id="new-user")

                        # Should get config prompt, not agent response
                        content = str(response.content) if hasattr(response, "content") else str(response)
                        assert "configure" in content.lower() or "jira" in content.lower()

    def test_toolkit_config_is_configured_check(self, shared_db, token_storage):
        """Test that toolkit configs properly check if they're configured."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")

        # All toolkits should report not configured for new user
        for config in _get_toolkit_configs(agent):
            assert not config.is_configured("brand-new-user"), (
                f"{config.__class__.__name__}.is_configured() should return False for new user"
            )


class TestAgentExecution:
    """Tests for agent execution with configured toolkits."""

    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    def test_sync_run(self, shared_db, token_storage):
        """Test synchronous run() method with all toolkits mocked as configured."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        configs = _get_toolkit_configs(agent)

        # Mock all toolkit configs as configured
        patches = [patch.object(c, "is_configured", return_value=True) for c in configs]
        for p in patches:
            p.start()
        try:
            response = agent.run("Hello! Can you help me?", user_id="test-user")
            assert response is not None
            assert hasattr(response, "content")
            assert len(str(response.content)) > 0
        finally:
            for p in patches:
                p.stop()


class TestAgentCaching:
    """Tests for agent caching and invalidation."""

    def test_agent_is_cached(self, shared_db, token_storage):
        """Test that agent is cached after first creation."""
        manager = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")

        # Create agent
        agent1 = manager._get_or_create_agent()
        assert agent1 is not None

        # Calling again should return cached agent
        agent1_again = manager._get_or_create_agent()
        assert agent1_again is agent1, "Should return cached agent"


class TestConfigurationValidation:
    """Tests for configuration validation and error handling."""

    def test_workbook_error_surfaces_in_instructions(self, shared_db, token_storage):
        """Test that workbook loading failures are surfaced in agent instructions.

        Simulates: service account is configured (is_configured=True) but the
        actual workbook download fails (get_toolkit raises RuntimeError).
        This is realistic — e.g., wrong URL, network error, unshared document.
        """
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        configs = _get_toolkit_configs(agent)

        # Find the ReleaseManagerToolkitConfig
        rm_config = next(c for c in configs if isinstance(c, ReleaseManagerToolkitConfig))

        # Simulate: service account credentials are present (infrastructure OK)
        # but workbook download fails (network error, wrong URL, etc.)
        # is_configured() now only checks infrastructure, so this is realistic.
        with patch.object(rm_config._gdrive_config, "is_configured", return_value=True):
            with patch.object(rm_config, "get_toolkit", side_effect=RuntimeError("Workbook download failed")):
                # Need workbook URL set for is_configured() to return True
                rm_config._workbook_url = "https://docs.google.com/spreadsheets/d/fake-id/edit"

                # Build instructions should include the warning
                instructions = agent._configurator._build_agent_instructions()
                instructions_text = "\n".join(instructions)
                assert "WARNING" in instructions_text
                assert "Workbook download failed" in instructions_text
                assert "without workbook configuration" in instructions_text


class TestToolkitInstructions:
    """Tests for toolkit-specific agent instructions."""

    def test_agent_instructions_empty_when_not_configured(self, shared_db, token_storage):
        """Test that toolkits don't add instructions when not configured."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")

        # Get instructions for unconfigured user
        for config in _get_toolkit_configs(agent):
            instructions = config.get_agent_instructions("unconfigured-user")
            # Should be empty since not configured
            assert len(instructions) == 0


class TestRequiredVsOptionalConfigs:
    """Tests for required toolkit configuration behavior."""

    def test_jira_config_is_required(self, shared_db, token_storage):
        """Test that JiraConfig is required (inherits from base)."""
        jira_config = JiraConfig(token_storage=token_storage)
        assert jira_config.is_required(), "JiraConfig should be required by default"

    def test_rm_toolkit_config_is_required(self, shared_db, token_storage):
        """Test that ReleaseManagerToolkitConfig is required."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")

        rm_config = next(c for c in _get_toolkit_configs(agent) if isinstance(c, ReleaseManagerToolkitConfig))
        assert rm_config.is_required(), "ReleaseManagerToolkitConfig should be required"

    @patch("agentllm.tools.jira_toolkit.JiraTools")
    def test_required_config_blocks_agent_until_configured(self, mock_jira_tools, shared_db, token_storage):
        """Test that required configs prevent agent usage until configured."""
        agent = ReleaseManager(shared_db=shared_db, token_storage=token_storage, user_id="test-user")
        configs = _get_toolkit_configs(agent)

        # Mock ReleaseManagerToolkitConfig as configured
        rm_config = next(c for c in configs if isinstance(c, ReleaseManagerToolkitConfig))
        with patch.object(rm_config, "is_configured", return_value=True):
            # Add a required config (JiraConfig is required by default)
            jira_config = JiraConfig(token_storage=token_storage)
            configs.append(jira_config)

            # Mock the prompt
            mock_jira_tools.return_value.validate_connection.return_value = (True, "Connected")

            # Try to use agent without configuring Jira
            response = agent.run("Hello!", user_id="new-user")

            # Should get JIRA config prompt, not agent response
            content = str(response.content) if hasattr(response, "content") else str(response)
            assert "jira" in content.lower() or "token" in content.lower()


# TestExtendedSystemPrompt tests removed - functionality moved to SystemPromptExtensionConfig
# and tested in test_system_prompt_extension_config.py
