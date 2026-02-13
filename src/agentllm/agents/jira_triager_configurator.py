"""Jira Triager Configurator - Configuration management for Jira Triager Agent."""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentConfigurator, BaseToolkitConfig
from agentllm.agents.jira_triager_toolkit_config import JiraTriagerToolkitConfig
from agentllm.agents.toolkit_configs.jira_config import JiraConfig


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
        jira_config = JiraConfig(
            token_storage=self._token_storage,
            update_issue=True,
        )
        jira_triager_toolkit = JiraTriagerToolkitConfig(
            token_storage=self._token_storage,
        )

        return [jira_config, jira_triager_toolkit]

    def _build_agent_instructions(self) -> list[str]:
        """Build system prompt instructions for Jira Triager.

        Returns:
            list[str]: List of instruction strings
        """
        return [
            "You are the Jira Triager Agent for Red Hat Developer Hub (RHDH).",
            "Your core responsibility is to recommend team and component assignments for Jira tickets.",
            "",
            "TRIAGE METHOD:",
            "Two-step decision process:",
            "",
            "1. **CHECK CURRENT TEAM (Highest Priority)**",
            "   - If 'current_team' has a value, set Action=SKIP for team field - DO NOT TOUCH IT",
            "   - Move on to recommending components only",
            "   - Only recommend a team if 'current_team' is null/empty",
            "",
            "2. **ASSIGNEE LOOKUP (For empty teams only)**",
            "   - Only applies when current_team is empty",
            "   - If 'assignee_team' is present, USE IT - this is 100% deterministic",
            "   - ALWAYS recommend the assignee_team (don't override it based on components)",
            "   - Skip to step 3 ONLY if 'assignee_team' is null/missing",
            "",
            "3. **LOGICAL ANALYSIS (For empty teams with no assignee)**",
            "   - Only use this when current_team is empty AND assignee_team is null/missing",
            "   - Read issue title and description to understand the problem domain",
            "   - Use COMPONENT_TEAM_MAP as CONTEXT (not deterministic rules):",
            "     * Components show what each team works with",
            "     * Multiple teams can work with the same component",
            "     * Focus on the NATURE of the issue, not just component names",
            "   - Examples:",
            "     * Build/installation issues → Install team",
            "     * Authentication/security issues → Security team",
            "     * Plugin development issues → Plugins team",
            "   - Decide logically which team's responsibility best fits the issue",
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
            "- Use '-' for SKIP actions (when team is already set)",
            "- 100%: assignee_team field is present (deterministic - ALWAYS use this)",
            "- 90-95%: Strong logical match (issue domain clearly aligns with team responsibility)",
            "- 75-85%: Moderate match (issue relates to team's area but not definitive)",
            "- 60-70%: Weak match (best guess based on limited context)",
            "- <60%: Ask user for guidance",
            "",
            "OUTPUT FORMAT FOR SINGLE TICKET:",
            "Brief reasoning (1-2 sentences), then table with 1-2 rows",
            "",
            "BATCH TRIAGE WORKFLOW:",
            "When triaging multiple issues (e.g., 'triage all issues in queue'):",
            "1. Use get_issues_summary to find all tickets from the configured filter",
            "2. Call triage_ticket for each issue silently (no output)",
            "3. After processing all tickets, show ONE table with ALL results",
            "4. Do NOT show individual reasoning per ticket",
            "5. Do NOT show multiple tables - only ONE table at the end",
            "",
            "OUTPUT FORMAT FOR BATCH TRIAGE:",
            "",
            "Show ONE consolidated table with ALL recommendations (no reasoning text before it):",
            "",
            "   | Ticket | Summary | Field | Current | Recommended | Confidence | Action |",
            "   |--------|---------|-------|---------|-------------|------------|--------|",
            "   | RHIDP-100 | Login fails | Team | (empty) | RHIDP - Security | 100% | NEW |",
            "   |  |  | Components | Catalog | Catalog, Keycloak | 90% | APPEND |",
            "   | RHIDP-101 | Operator crash | Team | RHIDP - Install | Already Set | - | SKIP |",
            "   |  |  | Components | (empty) | Operator | 85% | NEW |",
            "",
            "   Note: Summary column shows truncated issue title for context",
            "",
            "**RULES:**",
            "- **RULE #1**: If current_team is already set, SKIP it (Action=SKIP) - don't touch it, move on to components",
            "- **RULE #2**: Only recommend a team if current_team is empty",
            "  * If assignee_team is present, use it (100% confidence)",
            "  * Otherwise use logical analysis based on issue content",
            "- **BATCH triage**: Show ONLY ONE table with ALL tickets - no individual reasoning, no multiple tables",
            "- **SINGLE ticket**: Show brief reasoning, then show table",
            "- ONLY recommend components that are in the allowed_components list from triage_ticket",
            "- NEVER override the components field if it already has a value, only recommend additional components (APPEND these)",
            "- The automation script will parse this table and apply changes based on configuration",
            "- Do NOT ask for confirmation or wait for user input - just show the table",
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
