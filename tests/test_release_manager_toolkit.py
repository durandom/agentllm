"""Unit tests for ReleaseManagerToolkit.

Tests the toolkit methods in isolation using mock data (no agent, no APIs).
This is Level 0 of the test pyramid - fast, deterministic, focused on toolkit logic.

Run with: pytest tests/test_release_manager_toolkit.py -v
"""

import pytest

from agentllm.tools.release_manager_toolkit import ReleaseManagerToolkit


@pytest.fixture
def toolkit(mock_gdrive_workbook):
    """Create ReleaseManagerToolkit instance with mock workbook data."""
    return ReleaseManagerToolkit(sheets_data=mock_gdrive_workbook)


class TestReleaseManagerToolkitCore:
    """Test toolkit initialization and core functionality."""

    def test_initialization(self, mock_gdrive_workbook):
        """Test toolkit initializes with sheets data."""
        toolkit = ReleaseManagerToolkit(sheets_data=mock_gdrive_workbook)
        assert toolkit is not None
        assert toolkit._sheets == mock_gdrive_workbook
        assert toolkit.name == "release_manager_toolkit"

    def test_tool_registration(self, toolkit):
        """Test all 6 methods are registered as tools."""
        # ReleaseManagerToolkit should register 6 tools (get_response_format removed)
        expected_tool_count = 6
        assert len(toolkit.tools) == expected_tool_count

        # Verify tool names
        tool_names = {tool.__name__ for tool in toolkit.tools}
        expected_names = {
            "get_jira_query_template",
            "get_slack_template",
            "get_workflow_instructions",
            "get_project_config",
            "get_tool_reference",
            "get_prompt",  # NOTE: get_response_format removed (Response Formats sheet replaced by Prompts)
        }
        assert tool_names == expected_names

    def test_helper_methods_exist(self, toolkit):
        """Test helper methods are available but not registered as tools."""
        # Helper methods should exist
        assert hasattr(toolkit, "list_available_queries")
        assert hasattr(toolkit, "list_available_templates")
        assert hasattr(toolkit, "list_available_workflows")

        # Helper method names should NOT be in registered tools
        tool_names = {tool.__name__ for tool in toolkit.tools}
        assert "list_available_queries" not in tool_names
        assert "list_available_templates" not in tool_names
        assert "list_available_workflows" not in tool_names


class TestJiraQueryRetrieval:
    """Test get_jira_query_template() method."""

    def test_valid_query_returns_formatted_result(self, toolkit):
        """Test retrieving a valid query returns all fields."""
        result = toolkit.get_jira_query_template("jira list of active release")

        # Should contain all expected fields
        assert "**Query:** jira list of active release" in result
        assert "**Description:** Get all active releases" in result
        assert "**JQL Template:**" in result
        assert "project = RHDHPlan AND issuetype = Release AND status != Closed" in result
        assert "**Example:** Returns all open releases" in result

    def test_case_insensitive_lookup(self, toolkit):
        """Test query name lookup is case-insensitive."""
        # All these should work
        result1 = toolkit.get_jira_query_template("jira list of active release")
        result2 = toolkit.get_jira_query_template("Jira List Of Active Release")
        result3 = toolkit.get_jira_query_template("JIRA LIST OF ACTIVE RELEASE")

        # All should return the same query
        assert "jira list of active release" in result1
        assert "jira list of active release" in result2
        assert "jira list of active release" in result3

    def test_placeholder_preservation(self, toolkit):
        """Test that {{PLACEHOLDER}} syntax is preserved in templates."""
        result = toolkit.get_jira_query_template("jira list of open issues by type query template")

        # Should preserve double curly brace placeholders
        assert "{{RELEASE_VERSION}}" in result
        assert "{{ISSUE_TYPE}}" in result
        assert "**Placeholders:** {{RELEASE_VERSION}}, {{ISSUE_TYPE}}" in result

    def test_unknown_query_raises_error_with_available_list(self, toolkit):
        """Test that unknown query raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_jira_query_template("nonexistent query")

        error_msg = str(exc_info.value)
        assert "Query 'nonexistent query' not found" in error_msg
        assert "Available queries:" in error_msg
        # Should list all available query names
        assert "jira list of active release" in error_msg
        assert "jira list of open issues by type query template" in error_msg
        assert "jira list of blockers" in error_msg

    def test_empty_query_name_raises_error(self, toolkit):
        """Test that empty query name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_jira_query_template("")

        assert "not found" in str(exc_info.value)


class TestSlackTemplateRetrieval:
    """Test get_slack_template() method."""

    def test_valid_template_returns_content(self, toolkit):
        """Test retrieving a valid template returns all fields."""
        result = toolkit.get_slack_template("Feature Freeze Update")

        # Should contain all expected fields
        assert "**Template:** Feature Freeze Update" in result
        assert "**Milestone:** Feature Freeze" in result
        assert "**When to Send:** Before Feature Freeze date" in result
        assert "**Data Requirements:**" in result
        assert "Feature Freeze date, Active teams, Outstanding Release Notes count" in result
        assert "**Template Content:**" in result
        assert ":warning: *RHDH {{RELEASE_VERSION}} Feature Freeze*" in result

    def test_milestone_and_data_requirements_included(self, toolkit):
        """Test that milestone and data requirements are properly formatted."""
        result = toolkit.get_slack_template("Code Freeze Announcement")

        # Should have structured metadata
        assert "**Milestone:** Code Freeze" in result
        assert "**When to Send:** 1 week before Code Freeze" in result
        assert "**Data Requirements:**" in result
        assert "Code Freeze date, Open bugs count, Open features count" in result

    def test_placeholder_syntax_preserved(self, toolkit):
        """Test that template placeholders use {{PLACEHOLDER}} syntax."""
        result = toolkit.get_slack_template("Feature Freeze Update")

        # Should preserve double curly brace placeholders
        assert "{{RELEASE_VERSION}}" in result
        assert "{{FEATURE_FREEZE_DATE}}" in result
        assert "{{RELEASE_NOTES_COUNT}}" in result

    def test_case_insensitive_template_lookup(self, toolkit):
        """Test template name lookup is case-insensitive."""
        result1 = toolkit.get_slack_template("Feature Freeze Update")
        result2 = toolkit.get_slack_template("feature freeze update")
        result3 = toolkit.get_slack_template("FEATURE FREEZE UPDATE")

        # All should return the same template
        assert "Feature Freeze Update" in result1
        assert "Feature Freeze Update" in result2
        assert "Feature Freeze Update" in result3

    def test_unknown_template_raises_error_with_available_list(self, toolkit):
        """Test that unknown template raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_slack_template("Nonexistent Template")

        error_msg = str(exc_info.value)
        assert "Template 'Nonexistent Template' not found" in error_msg
        assert "Available templates:" in error_msg
        # Should list all available template names
        assert "Feature Freeze Update" in error_msg
        assert "Code Freeze Announcement" in error_msg


class TestWorkflowRetrieval:
    """Test get_workflow_instructions() method."""

    def test_workflow_instructions_formatted_correctly(self, toolkit):
        """Test retrieving workflow returns all structured fields."""
        result = toolkit.get_workflow_instructions("generate release status")

        # Should contain all workflow fields
        assert "**Workflow:** generate release status" in result
        assert "**Description:** Create weekly release status update" in result
        assert "**Required Input:** Release version" in result
        assert "**Data Sources:** Jira issues, Release schedule" in result
        assert "**Tools:** get_issues_stats, get_issues_summary" in result
        assert "**Output Format:** Release Status Update" in result
        assert "**Instructions:**" in result
        assert "1. Query open issues" in result
        assert "2. Calculate metrics" in result

    def test_all_fields_present(self, toolkit):
        """Test that all workflow fields are included when present."""
        result = toolkit.get_workflow_instructions("prepare freeze announcement")

        # Verify structure
        assert "**Workflow:**" in result
        assert "**Description:**" in result
        assert "**Required Input:**" in result
        assert "**Data Sources:**" in result
        assert "**Tools:**" in result
        assert "**Output Format:**" in result
        assert "**Instructions:**" in result

        # Verify content
        assert "Release version, Freeze date, Milestone type" in result
        assert "get_slack_template, get_issues_stats" in result
        assert "Slack Markdown" in result

    def test_case_insensitive_workflow_lookup(self, toolkit):
        """Test workflow name lookup is case-insensitive."""
        result1 = toolkit.get_workflow_instructions("generate release status")
        result2 = toolkit.get_workflow_instructions("Generate Release Status")
        result3 = toolkit.get_workflow_instructions("GENERATE RELEASE STATUS")

        # All should return the same workflow
        assert "generate release status" in result1
        assert "generate release status" in result2
        assert "generate release status" in result3

    def test_unknown_workflow_raises_error_with_available_list(self, toolkit):
        """Test that unknown workflow raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_workflow_instructions("nonexistent workflow")

        error_msg = str(exc_info.value)
        assert "Workflow 'nonexistent workflow' not found" in error_msg
        assert "Available workflows:" in error_msg
        # Should list all available workflow names
        assert "generate release status" in error_msg
        assert "prepare freeze announcement" in error_msg


class TestProjectConfig:
    """Test get_project_config() method."""

    def test_single_config_key_returns_value(self, toolkit):
        """Test retrieving a config key returns value and description."""
        result = toolkit.get_project_config("jira_default_base_jql")

        # Should contain config key
        assert "**Config:** jira_default_base_jql" in result

        # Should contain value and description
        assert "**Value:**" in result
        assert "project IN (RHIDP" in result  # Part of the JQL value
        assert "**Description:**" in result
        assert "Default JQL scope" in result

    def test_multiple_config_keys_available(self, toolkit):
        """Test that multiple config keys can be retrieved independently."""
        result1 = toolkit.get_project_config("jira_default_base_jql")
        result2 = toolkit.get_project_config("team_mapping_gdrive_id")

        # Both should work
        assert "jira_default_base_jql" in result1
        assert "team_mapping_gdrive_id" in result2

    def test_case_insensitive_config_key_lookup(self, toolkit):
        """Test config key lookup is case-insensitive."""
        result1 = toolkit.get_project_config("jira_default_base_jql")
        result2 = toolkit.get_project_config("JIRA_DEFAULT_BASE_JQL")
        result3 = toolkit.get_project_config("Jira_Default_Base_Jql")

        # All should return the same content (lookup is case-insensitive)
        assert "jira_default_base_jql" in result1
        assert "jira_default_base_jql" in result2
        assert "jira_default_base_jql" in result3

    def test_unknown_config_key_raises_error_with_available_list(self, toolkit):
        """Test that unknown config key raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_project_config("nonexistent_key")

        error_msg = str(exc_info.value)
        assert "Config key 'nonexistent_key' not found" in error_msg
        assert "Available keys:" in error_msg
        # Should list all available config keys
        assert "jira_default_base_jql" in error_msg
        assert "team_mapping_gdrive_id" in error_msg


class TestToolReference:
    """Test get_tool_reference() method."""

    def test_tool_documentation_complete(self, toolkit):
        """Test retrieving tool documentation returns all fields."""
        result = toolkit.get_tool_reference("get_issues_detailed")

        # Should contain all tool reference fields
        assert "**Tool:** get_issues_detailed" in result
        assert "**Category:** Jira" in result
        assert "**Parameters:** jql_query, fields=[], max_results=50" in result
        assert "**Returns:** List of issues with custom fields" in result
        assert "**Use When:** Need detailed issue info with custom fields" in result
        assert "**Example:**" in result
        assert "get_issues_detailed('project = RHIDP', ['summary', 'status'])" in result

    def test_parameters_and_examples_included(self, toolkit):
        """Test that parameters and examples are properly formatted."""
        result = toolkit.get_tool_reference("get_issues_summary")

        # Should have structured documentation
        assert "**Parameters:** jql_query, max_results=50" in result
        assert "**Returns:** Basic issue list (key, summary, status)" in result
        assert "**Use When:** Need simple issue listing" in result
        assert "**Example:** get_issues_summary('fixVersion = 1.9.0')" in result

    def test_case_insensitive_tool_lookup(self, toolkit):
        """Test tool name lookup is case-insensitive."""
        result1 = toolkit.get_tool_reference("get_issues_detailed")
        result2 = toolkit.get_tool_reference("Get_Issues_Detailed")
        result3 = toolkit.get_tool_reference("GET_ISSUES_DETAILED")

        # All should return the same tool
        assert "get_issues_detailed" in result1
        assert "get_issues_detailed" in result2
        assert "get_issues_detailed" in result3

    def test_unknown_tool_raises_error_with_available_list(self, toolkit):
        """Test that unknown tool raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_tool_reference("nonexistent_tool")

        error_msg = str(exc_info.value)
        assert "Tool 'nonexistent_tool' not found" in error_msg
        assert "Available tools:" in error_msg
        # Should list all available tool names
        assert "get_issues_detailed" in error_msg
        assert "get_issues_summary" in error_msg


# NOTE: TestResponseFormat class removed - get_response_format() method deleted
# Response Formats sheet replaced by Prompts sheet - see TestPromptMethods instead


class TestColumnNamingConventions:
    """Test that column naming conventions are respected."""

    def test_snake_case_columns_jira_queries(self, toolkit):
        """Test Jira Queries sheet uses snake_case columns."""
        # Should work with snake_case column names
        result = toolkit.get_jira_query_template("jira list of active release")
        assert result is not None

        # Verify it's using the 'name' column (snake_case)
        queries = toolkit.list_available_queries()
        assert "jira list of active release" in queries

    def test_snake_case_columns_slack_templates(self, toolkit):
        """Test Slack Templates sheet uses snake_case columns."""
        # Should work with snake_case column names
        result = toolkit.get_slack_template("Feature Freeze Update")
        assert result is not None

        # Verify template_content field (snake_case)
        assert "{{RELEASE_VERSION}}" in result
        assert "{{FEATURE_FREEZE_DATE}}" in result

    def test_snake_case_columns_workflows(self, toolkit):
        """Test Actions & Workflows sheet uses snake_case columns."""
        # Should work with snake_case column names
        result = toolkit.get_workflow_instructions("generate release status")
        assert result is not None

        # Verify snake_case fields
        assert "input_required" in result.lower() or "Required Input:" in result

    def test_snake_case_columns_config(self, toolkit):
        """Test Configuration & Setup sheet uses snake_case columns."""
        # Should work with snake_case column names
        result = toolkit.get_project_config("jira_default_base_jql")
        assert result is not None

        # Verify snake_case structure
        assert "**Config:**" in result
        assert "**Value:**" in result
        assert "**Description:**" in result

    def test_title_case_columns_tools(self, toolkit):
        """Test Tools Reference sheet uses Title Case columns."""
        # Should work with Title Case column names
        result = toolkit.get_tool_reference("get_issues_detailed")
        assert result is not None

        # Verify Title Case fields
        assert "**Tool Name:**" in result or "**Tool:**" in result
        assert "**Category:**" in result

    # NOTE: test_title_case_columns_formats removed - Response Formats sheet no longer exists

    def test_mixed_naming_does_not_break_lookup(self, toolkit):
        """Test that mixed naming conventions don't break lookups."""
        # All lookups should work regardless of naming convention
        assert toolkit.get_jira_query_template("jira list of active release") is not None
        assert toolkit.get_slack_template("Feature Freeze Update") is not None
        assert toolkit.get_workflow_instructions("generate release status") is not None
        assert toolkit.get_project_config("jira_default_base_jql") is not None  # Updated to use config_key
        assert toolkit.get_tool_reference("get_issues_detailed") is not None
        # NOTE: get_response_format removed - Response Formats sheet replaced by Prompts


class TestHelperMethods:
    """Test helper methods (not registered as tools)."""

    def test_list_available_queries_returns_all_names(self, toolkit):
        """Test list_available_queries() returns all query names."""
        queries = toolkit.list_available_queries()

        assert len(queries) == 3  # Mock workbook has 3 queries
        assert "jira list of active release" in queries
        assert "jira list of open issues by type query template" in queries
        assert "jira list of blockers" in queries

    def test_list_available_templates_returns_all_names(self, toolkit):
        """Test list_available_templates() returns all template names."""
        templates = toolkit.list_available_templates()

        assert len(templates) == 2  # Mock workbook has 2 templates
        assert "Feature Freeze Update" in templates
        assert "Code Freeze Announcement" in templates

    def test_list_available_workflows_returns_all_names(self, toolkit):
        """Test list_available_workflows() returns all workflow names."""
        workflows = toolkit.list_available_workflows()

        assert len(workflows) == 2  # Mock workbook has 2 workflows
        assert "generate release status" in workflows
        assert "prepare freeze announcement" in workflows

    def test_empty_sheets_return_empty_lists(self):
        """Test that empty sheets fail validation (schema validation requires data)."""
        # Toolkit now validates schema and requires all 7 sheets with proper structure
        # Empty sheets will fail validation
        empty_data = {
            "Jira Queries": [],
            "Slack Templates": [],
            "Actions & Workflows": [],
            "Configuration & Setup": [],
            "Tools Reference": [],
            "Prompts": [],  # NOTE: Changed from "Response Formats"
            "Maintenance Guide": [],
        }

        # Should raise ValueError during initialization due to empty sheets
        with pytest.raises(ValueError) as exc_info:
            ReleaseManagerToolkit(sheets_data=empty_data)

        error_msg = str(exc_info.value)
        assert "Workbook validation failed" in error_msg
        assert "is empty (no data rows)" in error_msg


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_unknown_query_raises_value_error(self, toolkit):
        """Test that unknown query raises ValueError."""
        with pytest.raises(ValueError):
            toolkit.get_jira_query_template("nonexistent")

    def test_missing_sheet_raises_value_error(self):
        """Test that missing sheet raises ValueError during initialization."""
        # Create toolkit with missing sheets - should fail validation immediately
        incomplete_data = {"Configuration & Setup": []}

        with pytest.raises(ValueError) as exc_info:
            ReleaseManagerToolkit(sheets_data=incomplete_data)

        error_msg = str(exc_info.value)
        assert "Workbook validation failed" in error_msg
        assert "Missing required sheet" in error_msg

    def test_empty_sheet_data_handled_gracefully(self):
        """Test that empty sheet data fails validation during initialization."""
        empty_data = {
            "Jira Queries": [],
            "Slack Templates": [],
            "Actions & Workflows": [],
            "Configuration & Setup": [],
            "Tools Reference": [],
            "Prompts": [],  # NOTE: Changed from "Response Formats"
            "Maintenance Guide": [],
        }

        # Should raise ValueError during initialization (schema validation)
        with pytest.raises(ValueError) as exc_info:
            ReleaseManagerToolkit(sheets_data=empty_data)

        error_msg = str(exc_info.value)
        assert "Workbook validation failed" in error_msg
        assert "is empty (no data rows)" in error_msg

    def test_error_messages_are_self_correcting(self, toolkit):
        """Test that error messages list available items for self-correction."""
        # Query error should list available queries
        try:
            toolkit.get_jira_query_template("bad_query")
        except ValueError as e:
            assert "Available queries:" in str(e)
            assert "jira list of active release" in str(e)

        # Template error should list available templates
        try:
            toolkit.get_slack_template("bad_template")
        except ValueError as e:
            assert "Available templates:" in str(e)
            assert "Feature Freeze Update" in str(e)

        # Workflow error should list available workflows
        try:
            toolkit.get_workflow_instructions("bad_workflow")
        except ValueError as e:
            assert "Available workflows:" in str(e)
            assert "generate release status" in str(e)

        # Config error should list available keys
        try:
            toolkit.get_project_config("bad_key")
        except ValueError as e:
            assert "Available keys:" in str(e)
            assert "jira_default_base_jql" in str(e)

        # Tool error should list available tools
        try:
            toolkit.get_tool_reference("bad_tool")
        except ValueError as e:
            assert "Available tools:" in str(e)
            assert "get_issues_detailed" in str(e)

        # NOTE: Response format error test removed - get_response_format() no longer exists
        # See TestPromptMethods for prompt error handling tests


class TestPromptMethods:
    """Test prompt retrieval methods."""

    def test_get_system_prompt(self, toolkit):
        """Test system prompt retrieval."""
        prompt = toolkit.get_system_prompt()

        assert prompt
        assert "Release Manager" in prompt or "RHDH" in prompt

    def test_get_system_prompt_missing(self, mock_gdrive_workbook):
        """Test error when system prompt missing."""
        # Create a workbook with Prompts sheet but no system prompt
        workbook_data = mock_gdrive_workbook.copy()
        workbook_data["Prompts"] = [{"name": "test", "prompt_type": "situational", "prompt_content": "Test"}]
        toolkit = ReleaseManagerToolkit(sheets_data=workbook_data)

        with pytest.raises(ValueError, match="No system prompt found"):
            toolkit.get_system_prompt()

    def test_get_prompt_success(self, toolkit):
        """Test situational prompt retrieval."""
        prompt = toolkit.get_prompt("feature_freeze_prep")

        assert prompt
        assert "Context" in prompt or "Feature Freeze" in prompt

    def test_get_prompt_case_insensitive(self, toolkit):
        """Test case-insensitive lookup."""
        prompt1 = toolkit.get_prompt("Feature_Freeze_Prep")
        prompt2 = toolkit.get_prompt("feature_freeze_prep")

        assert prompt1 == prompt2

    def test_get_prompt_not_found(self, toolkit):
        """Test error with available prompts list."""
        with pytest.raises(ValueError) as exc_info:
            toolkit.get_prompt("nonexistent")

        error = str(exc_info.value)
        assert "nonexistent" in error
        assert "Available prompts:" in error
        assert "feature_freeze_prep" in error

    def test_get_prompt_excludes_system(self, toolkit):
        """Test that get_prompt doesn't return system prompt."""
        with pytest.raises(ValueError, match="not found"):
            toolkit.get_prompt("system_prompt")

    def test_list_available_prompts(self, toolkit):
        """Test listing prompts (excludes system)."""
        prompts = toolkit.list_available_prompts()

        assert len(prompts) >= 3
        assert "feature_freeze_prep" in prompts
        assert "system_prompt" not in prompts  # Excluded
        assert prompts == sorted(prompts)  # Sorted

    def test_list_prompts_with_descriptions(self, toolkit):
        """Test prompts with descriptions."""
        prompts = toolkit.list_prompts_with_descriptions()

        assert len(prompts) >= 3
        assert any(name == "feature_freeze_prep" for name, _ in prompts)

        # Should have descriptions
        names_with_desc = [(n, d) for n, d in prompts if d]
        assert len(names_with_desc) > 0
