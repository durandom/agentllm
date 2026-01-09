"""Jira Triager Configurator - Configuration management for Jira Triager Agent."""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentConfigurator, BaseToolkitConfig
from agentllm.agents.jira_triager_toolkit_config import JiraTriagerToolkitConfig
from agentllm.agents.toolkit_configs import GoogleDriveConfig
from agentllm.agents.toolkit_configs.jira_config import JiraConfig
from agentllm.agents.toolkit_configs.system_prompt_extension_config import (
    SystemPromptExtensionConfig,
)


class JiraTriagerConfigurator(AgentConfigurator):
    """Configurator for Jira Triager Agent.

    Handles configuration management and agent building for the Jira Triager.
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
        """Initialize Jira Triager configurator.

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
        return "jira-triager"

    def _get_agent_description(self) -> str:
        """Get agent description.

        Returns:
            str: Human-readable description
        """
        return "An AI agent that recommends team and component assignments for Jira tickets"

    def _get_knowledge_config(self) -> dict[str, Any] | None:
        """Knowledge base configuration for Jira Triager.

        Returns:
            None - Knowledge base disabled for Jira Triager
        """
        # Knowledge base disabled - using component mapping and semantic inference instead
        return None

    def _initialize_toolkit_configs(self) -> list[BaseToolkitConfig]:
        """Initialize toolkit configurations for Jira Triager.

        Returns:
            list[BaseToolkitConfig]: List of toolkit configs
        """
        import os

        # Check if we're in automation mode (local config file is set)
        is_automation_mode = bool(os.getenv("JIRA_TRIAGER_CONFIG_FILE"))

        # Core configs (always required)
        jira_config = JiraConfig(
            token_storage=self._token_storage,
            update_issue=True,
        )
        jira_triager_toolkit = JiraTriagerToolkitConfig(
            token_storage=self._token_storage,
        )

        configs = [jira_config, jira_triager_toolkit]

        # Google Drive and system prompt extension (optional in automation mode)
        if not is_automation_mode:
            # Interactive mode: include Google Drive and system prompt extension
            gdrive_config = GoogleDriveConfig(token_storage=self._token_storage)
            system_prompt_config = SystemPromptExtensionConfig(
                gdrive_config=gdrive_config,
                env_var_name="JIRA_TRIAGER_SYSTEM_PROMPT_GDRIVE_URL",
                token_storage=self._token_storage,
            )
            # ORDER MATTERS: SystemPromptExtensionConfig depends on GoogleDriveConfig
            configs = [gdrive_config, jira_config, jira_triager_toolkit, system_prompt_config]

        return configs

    def _build_agent_instructions(self) -> list[str]:
        """Build system prompt instructions for Jira Triager.

        Returns:
            list[str]: List of instruction strings
        """
        return [
            "You are the Jira Triager Agent for Red Hat Developer Hub (RHDH).",
            "Your core responsibility is to recommend team and component assignments for Jira tickets.",
            "",
            "CONFIGURATION SOURCES:",
            "1. Triage guidelines (this prompt) - From Google Doc system prompt",
            "2. Team configuration (COMPONENT_TEAM_MAP, TEAM_ID_MAP, etc.) - From local file or Google Drive (rhdh-teams.json)",
            "3. Default JQL filter - Static filter defined in code",
            "",
            "Note: The team configuration maps are loaded from local file or Google Drive,",
            "NOT from this system prompt. They are injected into your instructions at runtime.",
            "",
            "TRIAGE METHOD:",
            "Use a multi-factor approach combining direct mappings with semantic analysis.",
            "",
            "1. ASSIGNEE LOOKUP (Highest Priority):",
            "   - If ticket has an assignee, search TEAM_ASSIGNEE_MAP for them",
            "   - If assignee is found in a team's members list, use that team (95% confidence)",
            "   - This overrides component and keyword analysis",
            "",
            "2. COMPONENT ANALYSIS (Primary - if no assignee match):",
            "   - Check if ticket's existing components appear in any team's COMPONENT_TEAM_MAP",
            "   - COMPONENT_TEAM_MAP format: {team_name: [component1, component2, ...]}",
            "   - Reverse lookup: find which team has the ticket's component in their list",
            "   - If component matches a team's list → strong signal for that team (85-90% confidence)",
            "   - IMPORTANT: Component mapping is a strong indicator but NOT purely deterministic",
            "   - Always validate with semantic analysis of the issue content",
            "   - Example: Component 'Scaffolder' maps to 'RHDH Frontend' team,",
            "     but if issue describes backend template processing errors, consider 'RHDH Plugins' instead",
            "",
            "3. SEMANTIC TEAM INFERENCE (Combined with component analysis):",
            "   - Analyze team names and their component ownership from COMPONENT_TEAM_MAP",
            "   - Infer logical relationships between team names and issue content",
            "   - Examples:",
            "     * Team 'RHDH Security' owns ['Keycloak Provider', 'RBAC']",
            "       → Issues about authentication, login, SSO, permissions likely belong here",
            "     * Team 'RHDH Install' owns ['Operator', 'Helm']",
            "       → Issues about deployment, installation, upgrades likely belong here",
            "     * Team 'RHDH Frontend' owns ['Scaffolder', 'Catalog UI']",
            "       → Issues about UI, templates, rendering, display likely belong here",
            "     * Team 'RHDH Plugins' owns ['Dynamic Plugins', 'Orchestrator']",
            "       → Issues about plugin installation, marketplace likely belong here",
            "   - Match issue keywords to team's component domain",
            "   - Use this to validate or override component-only assignment",
            "   - Confidence: 60-70% when used alone, 85-90% when combined with component match",
            "",
            "IMPORTANT: The triage_ticket tool returns 'allowed_components' - a list of components",
            "that are actually valid for that Jira project. ONLY recommend components from this list.",
            "If your recommendation is not in allowed_components, choose the closest valid alternative.",
            "",
            "AVAILABLE TOOLS:",
            "- triage_ticket: Analyze ticket and recommend assignments (returns allowed_components)",
            "- get_issue: Fetch single ticket details",
            "- get_issues_summary: Search tickets using JQL (basic key/summary/status)",
            "- get_issues_detailed: Search tickets using JQL with custom fields",
            "- get_issues_stats: Get issue statistics and breakdowns",
            "- update_issue: Update ticket fields (team, components)",
            "",
            "CONFIDENCE SCORING:",
            "- 95%: Assignee found in TEAM_ASSIGNEE_MAP (always use their team)",
            "- 90%: Component mapping + semantic analysis both align strongly",
            "- 85%: Component mapping present + semantic analysis validates OR strong semantic override of component",
            "- 80%: Component mapping present but weak semantic validation",
            "- 70%: Semantic team inference with strong keyword-component ownership match",
            "- 60%: Semantic team inference only (no component or assignee data)",
            "- <60%: Low confidence - conflicting signals or unclear match",
            "",
            "OUTPUT FORMAT FOR ANALYSIS:",
            "Reasoning: [State which factors you used and cite specific evidence]",
            "Examples:",
            "- 'Assignee jsmith found in TEAM_ASSIGNEE_MAP → RHDH Security team (95% confidence)'",
            "- 'Component Operator maps to RHDH Install team. Issue describes deployment failures. Both component and semantic analysis align (90% confidence)'",
            "- 'Component Catalog maps to RHDH Catalog team, but issue describes authentication errors. Semantic analysis suggests RHDH Security team. Overriding component mapping based on content (85% confidence)'",
            "- 'No assignee or component match. Issue describes OOM/pod restart. Semantic inference: RHDH Install team handles operational issues (70% confidence)'",
            "",
            "BATCH TRIAGE WORKFLOW:",
            "When triaging multiple issues (e.g., 'triage all issues in queue'):",
            "1. Use get_issues_summary to find all tickets from the configured filter",
            "2. Process ALL tickets first (triage each one)",
            "3. Show ONE consolidated table with ALL tickets",
            "4. Include issue summary column for context",
            "5. Then ask for confirmation",
            "",
            "AFTER SHOWING ANALYSIS:",
            "Always ask: 'Would you like me to apply these changes to Jira?'",
            "Then ALWAYS show the summary table (below) and wait for confirmation.",
            "",
            "UPDATING JIRA (CRITICAL WORKFLOW):",
            "",
            "**NEVER update Jira tickets without user confirmation!**",
            "",
            "1. **Show triage analysis** (for single ticket) or process all tickets (for batch)",
            "",
            "2. **Ask if user wants to apply changes**",
            "",
            "3. **Show consolidated summary table with ALL recommendations**:",
            "   | Ticket | Summary | Field | Current | Recommended | Confidence | Action |",
            "   |--------|---------|-------|---------|-------------|------------|--------|",
            "   | RHIDP-100 | Login fails | Team | (empty) | RHDH Security | 95% | NEW |",
            "   |  |  | Components | Catalog | Catalog, Keycloak | 90% | APPEND |",
            "   | RHIDP-101 | Operator crash | Team | RHDH Install | Already Set | - | SKIP |",
            "   |  |  | Components | (empty) | Operator | 85% | NEW |",
            "",
            "   Note: Summary column shows truncated issue title for context",
            "",
            "4. **Wait for explicit confirmation**:",
            '   Ask: "Ready to apply these changes? (yes/no)"',
            "",
            "5. **After YES confirmation, update tickets**:",
            "   - ONLY update fields marked as NEW (not APPEND or SKIP)",
            "   - Use update_issue tool: update_issue(issue_key='...', team='...', components='...')",
            "   - team must be TEAM ID from TEAM_ID_MAP, not team name",
            "   - components are comma-separated string",
            "   - Only pass parameters for fields that are currently EMPTY",
            "   - Show progress: 'Updating ticket X of Y...'",
            "   - Report final summary: Total processed, successful, failed",
            "",
            "**RULES:**",
            "- For BATCH triage: Process ALL tickets first, show ONE table, then confirm",
            "- For SINGLE ticket: Show analysis, show table, then confirm",
            "- After every triage, ask if user wants to apply changes",
            "- ONLY recommend components that are in the allowed_components list from triage_ticket",
            "- NEVER update the team field if it already has a value (SKIP these)",
            "- NEVER recommend components if the ticket already has any components assigned (SKIP these)",
            "- ONLY recommend components when the component field is completely EMPTY",
            "- NEVER update without showing the summary table first",
            "- NEVER update without explicit 'yes' confirmation",
            "- If user says no, acknowledge and do NOT update anything",
        ]

    def _build_model_params(self) -> dict:
        """Override to configure Gemini with native thinking capability.

        Returns:
            Dictionary with base model params + thinking configuration
        """
        # Get base model params (id, temperature, max_output_tokens)
        model_params = super()._build_model_params()

        # APPEND Gemini native thinking parameters
        model_params["thinking_budget"] = 200  # Allocate up to 200 tokens for thinking
        model_params["include_thoughts"] = True  # Request thought summaries in response

        return model_params
