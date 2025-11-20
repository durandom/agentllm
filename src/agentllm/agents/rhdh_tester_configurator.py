"""RHDH Tester Agent Configurator - Configuration management for RHDH Tester Agent."""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentConfigurator, BaseToolkitConfig
from agentllm.agents.toolkit_configs.github_config import GitHubConfig


class RHDHTesterConfigurator(AgentConfigurator):
    """Configurator for RHDH Tester Agent.

    Handles configuration management and agent building for the RHDH Tester Agent.
    """

    def __init__(
        self,
        user_id: str,
        session_id: str | None,
        shared_db: SqliteDb,
        token_storage,
        temperature: float | None = None,
        max_tokens: int | None = None,
        agent_kwargs: dict[str, Any] | None = None,
        **model_kwargs: Any,
    ):
        """Initialize RHDH Tester Agent configurator.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            token_storage: TokenStorage instance
            temperature: Optional model temperature
            max_tokens: Optional max tokens
            agent_kwargs: Additional Agent constructor kwargs
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for use in _initialize_toolkit_configs
        self._token_storage = token_storage

        # Call parent constructor
        super().__init__(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_kwargs=agent_kwargs,
            **model_kwargs,
        )

    def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
        """Initialize toolkit configurations for RHDH Tester Agent.

        Returns:
            List of toolkit configuration instances
        """
        # Specify only PR creation/file manipulation tools
        pr_creation_tools = [
            "get_file",
            "list_directory",
            "get_branch_info",
            "create_branch",
            "create_or_update_file",
            "create_pull_request",
            "add_pr_comment",
            "sync_fork",
            "create_fork",
            "get_user_info",
        ]
        return [
            GitHubConfig(token_storage=self._token_storage, tools=pr_creation_tools),
        ]

    def _get_agent_name(self) -> str:
        """Return agent name."""
        return "rhdh-tester"

    def _get_agent_description(self) -> str:
        """Return agent description."""
        return "RHDH Tester - Creates and configures Red Hat Developer Hub test instances"

    def _get_model_id(self) -> str:
        """Override to use Gemini 3.0 Pro Preview.

        Returns:
            Model ID
        """
        return "gemini-2.5-pro"

    def _build_agent_instructions(self) -> list[str]:
        """Build agent-specific instructions for RHDH Tester Agent.

        Returns:
            List of instruction strings
        """
        return [
            "You are an RHDH (Red Hat Developer Hub) Tester agent that creates test instances by automating the PR workflow.",
            "RHDH is opinionated Backstage application with support for Dynamic Plugins and other features.",
            "",
            "## Core Responsibility",
            "Your goal is to create a new PR that configures RHDH according to the user's requirements. This involves reading existing config, merging new settings, and deploying via PR.",
            "",
            "## Workflow & Repository Management",
            "1. **Identify User's Fork**: Check if the user has a fork of `rhdh-test-instance`.",
            "   - First, try to check directly if `{username}/rhdh-test-instance` exists using `get_branch_info(repo='{username}/rhdh-test-instance', branch='main')`.",
            "   - **IF FOUND**: This is your `FORK` (e.g., `username/rhdh-test-instance`). Proceed to step 3.",
            "   - **IF NOT FOUND**: Ask the user if they have a fork with a different name.",
            "     - If they provide a name, verify it.",
            "     - If they don't have one, ask for permission to create it.",
            "2. **Create Fork (If Needed)**:",
            "   - If user agrees, use `create_fork(owner='redhat-developer', repo='rhdh-test-instance')`.",
            "   - This is your `FORK`.",
            "3. **Sync Fork**: Ensure the user's fork is up to date with upstream main.",
            "   - Use `sync_fork(repo=FORK, branch='main')`.",
            "4. **Parse Requirements**: Understand what Backstage/RHDH features the user wants.",
            "5. **Read Config**: Read current configuration from UPSTREAM `main` branch (to ensure freshness).",
            "   - UPSTREAM: `redhat-developer/rhdh-test-instance`",
            "   - `config/app-config-rhdh.yaml`",
            "   - `config/dynamic-plugins.yaml`",
            "6. **Merge Configuration**: Intelligent YAML merging.",
            "   - Preserve essential infrastructure settings.",
            "   - Add or modify sections as requested.",
            "   - Ensure valid YAML syntax.",
            "7. **Create Branch on Fork**: Create a new branch on the FORK from `main`.",
            "   - Name format: `test-instance/{description}-{timestamp}`",
            "8. **Commit to Fork**: Write the merged configuration files to the new branch on the FORK.",
            "9. **Open PR on Upstream**: Create a Pull Request on the UPSTREAM repository.",
            "   - `repo`: `redhat-developer/rhdh-test-instance`",
            "   - `head`: `username:branch_name` (where username is the fork owner)",
            "   - `base`: `main`",
            "10. **Trigger Deployment**: IMMEDIATELY after creating the PR, add a comment `/test deploy helm 1.7 4h` to the PR.",
            "11. **Report**: Inform the user of the PR URL and deployment status.",
            "",
            "## Configuration Guidelines",
            "- **app-config-rhdh.yaml**: Contains auth providers, catalog locations, techdocs, and general app settings.",
            "- **dynamic-plugins.yaml**: Lists enabled plugins and their specific configuration.",
            "- Do not delete existing unrelated configuration unless explicitly asked.",
            "",
            # "## Tool Usage",
            # "- `create_fork(owner='redhat-developer', repo='rhdh-test-instance')`",
            # "- `sync_fork(repo=FORK, branch='main')`",
            # "- `get_file(repo=UPSTREAM, ...)`",
            # "- `create_branch(repo=FORK, base_branch='main', new_branch_name=...)`",
            # "- `create_or_update_file(repo=FORK, ...)`",
            # "- `create_pull_request(repo=UPSTREAM, head='username:branch', base='main', ...)`",
            # "- `add_pr_comment(repo=UPSTREAM, pr_number=..., comment='/test')`",
            # "",
            "## Error Handling",
            "- If fork creation fails, ask user to fork manually.",
            "- If fork sync fails, ask user to sync manually or check permissions.",
            "- If file doesn't exist, report error.",
            "- If branch creation fails, try different name.",
        ]

    def _build_model_params(self) -> dict[str, Any]:
        """Override to configure Gemini with native thinking capability.

        Returns:
            Dictionary with base model params + thinking configuration
        """
        # Get base model params
        model_params = super()._build_model_params()

        # Add Gemini native thinking parameters
        # Higher budget for complex YAML merging logic
        model_params["thinking_budget"] = 300
        model_params["include_thoughts"] = True
        
        # Lower temperature for deterministic config generation
        model_params["temperature"] = 0.3

        return model_params

    def _get_agent_kwargs(self) -> dict[str, Any]:
        """Get agent kwargs without Agno's reasoning agent.

        Returns:
            Dictionary with base defaults
        """
        # Get base defaults
        kwargs = super()._get_agent_kwargs()

        # DO NOT set reasoning=True - we use Gemini's native thinking
        return kwargs
