"""Release Manager Configurator - Configuration management for Release Manager Agent."""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentConfigurator, BaseToolkitConfig
from agentllm.agents.toolkit_configs import GoogleDriveConfig
from agentllm.agents.toolkit_configs.jira_config import JiraConfig
from agentllm.agents.toolkit_configs.release_manager_toolkit_config import (
    ReleaseManagerToolkitConfig,
)
from agentllm.tools.release_manager_toolkit import ReleaseManagerToolkit


class ReleaseManagerConfigurator(AgentConfigurator):
    """Configurator for Release Manager Agent.

    Handles configuration management and agent building for the Release Manager.
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
        local_sheets_dir: str | None = None,
        **model_kwargs: Any,
    ):
        """Initialize Release Manager configurator.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            token_storage: TokenStorage instance
            temperature: Optional model temperature
            max_tokens: Optional max tokens
            agent_kwargs: Additional Agent constructor kwargs
            local_sheets_dir: Optional local directory with CSV sheets (for testing without OAuth)
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for use in _initialize_toolkit_configs
        self._token_storage = token_storage
        self._local_sheets_dir = local_sheets_dir

        # Call parent constructor (will call _initialize_toolkit_configs)
        super().__init__(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_kwargs=agent_kwargs,
            **model_kwargs,
        )

    def _get_agent_name(self) -> str:
        """Get agent name for identification.

        Returns:
            str: Agent name
        """
        return "release-manager"

    def _get_agent_description(self) -> str:
        """Get agent description.

        Returns:
            str: Human-readable description
        """
        return "A helpful AI assistant"

    def _get_model_id(self) -> str:
        """Get model ID for Release Manager.

        Can be overridden via RELEASE_MANAGER_MODEL environment variable.

        For available Gemini models, see:
        https://ai.google.dev/gemini-api/docs/models/gemini

        Available models:
        - gemini-3-pro-preview (default, best for complex reasoning)
        - gemini-2.5-pro (stable, production-ready)
        - gemini-2.5-flash (faster, good for simple queries)

        Returns:
            str: Model ID from env var or default (gemini-3-pro-preview)
        """
        import os

        # Allow override via environment variable
        model = os.getenv("RELEASE_MANAGER_MODEL")
        if model:
            from loguru import logger

            logger.info(f"Using model from RELEASE_MANAGER_MODEL env var: {model}")
            return model

        # Default to Gemini 3 Pro Preview
        return "gemini-3-pro-preview"

    def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
        """Initialize toolkit configurations for Release Manager.

        Returns:
            list[BaseToolkitConfig]: List of toolkit configs
        """
        # ORDER MATTERS: ReleaseManagerToolkitConfig depends on GoogleDriveConfig
        gdrive_config = GoogleDriveConfig(token_storage=self._token_storage)

        # Release Manager workbook (depends on GoogleDrive for OAuth, unless using local sheets)
        # We need to create this BEFORE JiraConfig so we can read jira_default_base_jql from the workbook
        rm_toolkit_config = ReleaseManagerToolkitConfig(
            gdrive_config=gdrive_config,
            local_sheets_dir=self._local_sheets_dir,
        )

        # Get jira_default_base_jql from workbook config (REQUIRED, no fallback)
        # If workbook is not configured or missing required keys, the configuration
        # conversation will prompt the user via rm_toolkit_config.get_config_prompt()
        default_base_jql = ""
        if rm_toolkit_config.is_configured(self.user_id):
            rm_toolkit = rm_toolkit_config.get_toolkit(self.user_id)
            config_values = rm_toolkit.get_all_config_values()
            default_base_jql = config_values.get("jira_default_base_jql", "")

        # Configure Jira with Release Manager specific base JQL from workbook
        # The default_base_jql is applied to queries that need base scoping
        # (like get_issues_by_team) to scope to RHDH projects and filter by status
        jira_config = JiraConfig(
            token_storage=self._token_storage,
            default_base_jql=default_base_jql,
        )

        return [
            gdrive_config,
            jira_config,
            rm_toolkit_config,  # Must come after gdrive_config due to dependency
        ]

    def _build_agent_instructions(self) -> list[str]:
        """Build system prompt instructions for Release Manager.

        Constructs instructions from:
        1. Hardcoded core instructions
        2. Reference data (available queries, templates, workflows with descriptions)

        Returns:
            list[str]: List of instruction strings
        """
        # 1. Start with hardcoded core instructions
        core_instructions = [
            "You are the Release Manager for Red Hat Developer Hub (RHDH).",
            "Your core responsibilities include:",
            "- Managing Y-stream releases (major versions like 1.7.0, 1.8.0)",
            "- Managing Z-stream releases (maintenance versions like 1.6.1, 1.6.2)",
            "- Tracking release progress, risks, and blockers",
            "- Coordinating with Engineering, QE, Documentation, and Product Management teams",
            "- Providing release status updates for meetings (SOS, Team Forum, Program Meeting)",
            "- Monitoring Jira for release-related issues, features, and bugs",
            "",
            "Output guidelines:",
            "- Use markdown formatting for all structured output",
            "- Be concise but comprehensive in your responses",
            "- Provide data-driven insights with Jira query results and metrics",
            "- Include relevant links to Jira issues, and Google Docs resources",
            "- Use tables and bullet points for clarity",
            "",
            "Behavioral guidelines:",
            "- Proactively identify risks and blockers",
            "- Escalate critical issues with clear impact analysis",
            "- Base recommendations on concrete data (Jira metrics, test results, schedules)",
            "- Maintain professional communication appropriate for cross-functional stakeholders",
            "- Follow established release processes and policies",
        ]

        # 2. Append workbook system_prompt
        rm_toolkit = self._get_rm_toolkit()
        if rm_toolkit:
            try:
                system_prompt = rm_toolkit.get_system_prompt()
                core_instructions.append("")
                core_instructions.append("## Additional Guidance from Workbook")
                core_instructions.append(system_prompt)
            except ValueError as e:
                # Log warning but continue (workbook optional for now)
                from loguru import logger

                logger.warning(f"Could not load system prompt from workbook: {e}")

        # 2.5 Inject configuration values from workbook
        if rm_toolkit:
            config_section = self._build_config_section(rm_toolkit)
            if config_section:
                core_instructions.append("")
                core_instructions.append(config_section)

        # 3. Append workflow enforcement (CRITICAL - before reference data)
        if rm_toolkit:
            enforcement = self._build_workflow_enforcement(rm_toolkit)
            if enforcement:
                core_instructions.append("")
                core_instructions.append(enforcement)

        # 4. Append reference data (available queries, templates, workflows)
        if rm_toolkit:
            reference_data = self._build_reference_data(rm_toolkit)
            if reference_data:
                core_instructions.append("")
                core_instructions.append("## Available Resources")
                core_instructions.append(reference_data)

            # 5. Append situational prompts reference
            prompts_reference = self._build_prompts_reference(rm_toolkit)
            if prompts_reference:
                core_instructions.append("")
                core_instructions.append(prompts_reference)

        return core_instructions

    def _get_rm_toolkit(self) -> ReleaseManagerToolkit | None:
        """Get Release Manager toolkit if configured.

        Returns:
            ReleaseManagerToolkit instance or None if not configured.
        """
        try:
            # Find ReleaseManagerToolkitConfig in toolkit_configs
            for config in self.toolkit_configs:
                if isinstance(config, ReleaseManagerToolkitConfig):
                    if config.is_configured(self.user_id):
                        return config.get_toolkit(self.user_id)
                    break
        except Exception as e:
            # Log but don't fail - just skip enhanced instructions
            from loguru import logger

            logger.warning(f"Could not load Release Manager toolkit: {e}")

        return None

    def _build_config_section(self, rm_toolkit: ReleaseManagerToolkit) -> str:
        """Build configuration values section for system prompt.

        Args:
            rm_toolkit: Release Manager toolkit instance.

        Returns:
            Formatted configuration section with all config key-value pairs.
        """
        config_values = rm_toolkit.get_all_config_values()
        if not config_values:
            return ""

        lines = ["## Configuration Values", ""]
        lines.append("The following configuration values are defined in the workbook:")
        lines.append("")

        for key, value in config_values.items():
            lines.append(f"- **{key}**: `{value}`")

        return "\n".join(lines)

    def _build_reference_data(self, rm_toolkit: ReleaseManagerToolkit) -> str:
        """Build reference data listing available resources with descriptions.

        Token-efficient format: `name` - description (when to use)

        Args:
            rm_toolkit: Release Manager toolkit instance.

        Returns:
            Formatted reference data with available queries, templates, workflows and descriptions.
        """
        queries = rm_toolkit.list_queries_with_descriptions()
        templates = rm_toolkit.list_templates_with_descriptions()
        workflows = rm_toolkit.list_workflows_with_descriptions()

        lines = []
        if queries:
            lines.append("**Jira Query Templates** (use `get_jira_query_template(query_name)`):")
            for name, desc in queries:
                if desc:
                    lines.append(f"- `{name}` - {desc}")
                else:
                    lines.append(f"- `{name}`")
            lines.append("")

        if templates:
            lines.append("**Slack Templates** (use `get_slack_template(template_name)`):")
            for name, when_to_send in templates:
                if when_to_send:
                    lines.append(f"- `{name}` - {when_to_send}")
                else:
                    lines.append(f"- `{name}`")
            lines.append("")

        if workflows:
            lines.append("**Workflows** (use `get_workflow_instructions(action_name)`):")
            for name, desc in workflows:
                if desc:
                    lines.append(f"- `{name}` - {desc}")
                else:
                    lines.append(f"- `{name}`")

        return "\n".join(lines)

    def _build_prompts_reference(self, rm_toolkit: ReleaseManagerToolkit) -> str:
        """Build reference list of situational prompts.

        Args:
            rm_toolkit: Release Manager toolkit instance

        Returns:
            Formatted markdown list of prompts with descriptions
        """
        prompts = rm_toolkit.list_prompts_with_descriptions()
        if not prompts:
            return ""

        lines = ["## Situational Prompts"]
        lines.append("")
        lines.append("Use `get_prompt(prompt_name)` to fetch detailed guidance for:")
        lines.append("")

        for name, desc in prompts:
            if desc:
                lines.append(f"- `{name}` - {desc}")
            else:
                lines.append(f"- `{name}`")

        return "\n".join(lines)

    def _build_workflow_enforcement(self, rm_toolkit: ReleaseManagerToolkit) -> str:
        """Build workflow-first enforcement framework.

        Generates prescriptive instructions that force the agent to check workflows
        before using direct Jira tools. Uses actual workflow data to build pattern
        matching table.

        Args:
            rm_toolkit: Release Manager toolkit instance

        Returns:
            Formatted enforcement framework as markdown string
        """
        # Get available workflows
        workflows = rm_toolkit.list_workflows_with_descriptions()
        if not workflows:
            return ""

        # Build pattern matching table from workflow names
        # Map common user query patterns to workflow names
        # NOTE: When adding new workflows to the workbook, update this map
        pattern_map = {
            "Retrieve Blocker Bugs": [
                '"blocker bugs"',
                '"blocker issues"',
                '"blockers"',
            ],
            "Retrieve list of CVEs": [
                '"CVEs"',
                '"vulnerabilities"',
                '"security issues"',
            ],
            "Retrieve Engineering EPICs": [
                '"EPICs"',
                '"open epics"',
                '"engineering epics"',
            ],
            "Retrieve outstanding Release Notes": [
                '"release notes"',
                '"missing release notes"',
            ],
            "Retrieve Issues by Engineering Teams": [
                '"team breakdown"',
                '"issues by team"',
                '"team counts"',
            ],
            "Announce Feature Freeze": [
                '"feature freeze"',
                '"feature freeze announcement"',
            ],
            "Announce Code Freeze": ['"code freeze"', '"code freeze announcement"'],
        }

        lines = ["## ⚠️ CRITICAL: WORKFLOW-FIRST DECISION FRAMEWORK", ""]
        lines.append("Before using ANY Jira tool directly, you MUST follow this decision process:")
        lines.append("")

        # Step 1: Pattern Recognition
        lines.append("### 1. Pattern Recognition")
        lines.append("Identify if the user's query matches a known workflow:")
        lines.append("")

        for workflow_name, patterns in pattern_map.items():
            # Check if this workflow actually exists in the workbook
            if any(name.strip() == workflow_name for name, _ in workflows):
                pattern_str = " / ".join(patterns)
                lines.append(f'- {pattern_str} → `get_workflow_instructions("{workflow_name}")`')

        lines.append("")

        # Step 2: Mandatory Check
        lines.append("### 2. MANDATORY Workflow Check")
        lines.append("If pattern matches:")
        lines.append("- Call `get_workflow_instructions(action_name)` FIRST")
        lines.append("- Do NOT skip to direct Jira queries")
        lines.append("")

        # Step 3: Execute Exactly
        lines.append("### 3. Execute Workflow EXACTLY")
        lines.append("Follow ALL workflow steps including:")
        lines.append("- Use query templates referenced (e.g., 'jira list of open issues' as base)")
        lines.append("- Use tools specified (e.g., `get_issues_detailed` vs `get_issues_summary`)")
        lines.append("- Apply correct project scope (often multi-project: RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP)")
        lines.append("- Follow output format requirements")
        lines.append("")

        # Step 4: Fallback
        lines.append("### 4. ONLY if NO Workflow Exists")
        lines.append("- Check for query template: `get_jira_query_template(query_name)`")
        lines.append("- Last resort: construct custom JQL query")
        lines.append("")

        # Examples
        lines.append("### Examples")
        lines.append("")
        lines.append("**❌ INCORRECT** (violation):")
        lines.append("```")
        lines.append('User: "Are there blocker bugs?"')
        lines.append('Agent: get_issues_summary(jql="project=RHDHPLAN AND priority=Blocker")')
        lines.append("Problem: Skipped workflow, missed multi-project scope, wrong tool")
        lines.append("```")
        lines.append("")
        lines.append("**✅ CORRECT**:")
        lines.append("```")
        lines.append('User: "Are there blocker bugs?"')
        lines.append('Agent: get_workflow_instructions("Retrieve Blocker Bugs")')
        lines.append("Agent: Follows workflow steps (uses 'jira list of open issues' template + filters)")
        lines.append("Agent: Uses get_issues_detailed() as specified")
        lines.append("Result: Multi-project query, complete data, standardized approach")
        lines.append("```")

        return "\n".join(lines)

    def _build_model_params(self) -> dict[str, Any]:
        """Build model parameters with Gemini native thinking capability.

        Returns:
            dict: Model configuration parameters
        """
        params = super()._build_model_params()

        # Add Gemini native thinking parameters
        params["thinking_budget"] = 200  # Allocate up to 200 tokens for thinking
        params["include_thoughts"] = True  # Request thought summaries in response

        return params
