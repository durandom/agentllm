"""
Release Manager toolkit for querying Excel workbook sheets.

Provides query methods for accessing structured data from the Release Manager
workbook including Jira queries, Slack templates, workflows, and configuration.
"""

from agno.tools import Toolkit

# Required sheets and their columns
SHEET_SCHEMA = {
    "Jira Queries": {
        "required": ["name", "jql_template"],
        "optional": ["description", "placeholders", "example", "notes", "trigger_phrases"],
    },
    "Slack Templates": {
        "required": ["name", "template_content"],
        "optional": ["milestone", "when_to_send", "data_requirements", "trigger_phrases"],
    },
    "Actions & Workflows": {
        "required": ["name", "instructions"],
        "optional": ["description", "input_required", "data_sources", "tools", "output_format", "trigger_phrases"],
    },
    "Configuration & Setup": {
        "required": ["config_key", "value"],
        "optional": ["description"],
    },
    "Tools Reference": {
        "required": ["Tool Name"],
        "optional": ["Category", "Parameters", "Returns", "Use When", "Example"],
    },
    "Maintenance Guide": {
        "required": ["Category", "Topic"],
        "optional": ["Guideline/Issue", "Recommendation/Solution", "Example", "Reference"],
    },
    "Prompts": {  # NOTE: Replaces "Response Formats" sheet
        "required": ["name", "prompt_content"],
        "optional": ["description", "prompt_type", "context"],
    },
}


class ReleaseManagerToolkit(Toolkit):
    """Toolkit for querying Release Manager workbook sheets.

    Provides methods to retrieve:
    - Jira query templates from "Jira Queries" sheet
    - Slack announcement templates from "Slack Templates" sheet
    - Workflow instructions from "Actions & Workflows" sheet
    - Project configuration from "Configuration & Setup" sheet
    - Tool documentation from "Tools Reference" sheet
    - Situational prompts from "Prompts" sheet
    """

    def __init__(self, sheets_data: dict[str, list[dict[str, str]]], **kwargs):
        """Initialize toolkit with parsed workbook sheets data.

        Args:
            sheets_data: Dictionary mapping sheet names to list of row dicts.
                Each row is a dict mapping column headers to cell values.
            **kwargs: Additional arguments passed to parent Toolkit.

        Raises:
            ValueError: If required sheets or columns are missing.
        """
        # Validate sheets and columns before proceeding
        self._validate_workbook_schema(sheets_data)

        self._sheets = sheets_data

        # Register all tools
        tools = [
            self.get_jira_query_template,
            self.get_slack_template,
            self.get_workflow_instructions,
            self.get_project_config,
            self.get_tool_reference,
            self.get_prompt,  # Replaced get_response_format (Response Formats sheet removed)
        ]

        super().__init__(name="release_manager_toolkit", tools=tools, **kwargs)

    def get_jira_query_template(self, query_name: str) -> str:
        """Get JQL query template from Jira Queries sheet.

        Returns the description, JQL template, and example for the specified query.
        Query templates use {{PLACEHOLDER}} syntax (double curly braces).

        To discover available queries: If you don't know the query name, provide an
        invalid name (e.g., "list") and the error message will return a formatted list
        of all available query names.

        Args:
            query_name: Name of the query to retrieve (case-insensitive).

        Returns:
            Formatted string with query details.

        Raises:
            ValueError: If query_name not found. Error message includes comma-separated
                list of all available query names for easy discovery.
        """
        sheet_name = "Jira Queries"
        sheet_data = self._sheets.get(sheet_name, [])

        if not sheet_data:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

        # Search for query (case-insensitive on 'name' column - lowercase snake_case)
        query_name_lower = query_name.lower().strip()
        for row in sheet_data:
            name = row.get("name", "").strip().lower()
            if name == query_name_lower:
                description = row.get("description", "").strip()
                jql_template = row.get("jql_template", "").strip()
                placeholders = row.get("placeholders", "").strip()
                example = row.get("example", "").strip()
                notes = row.get("notes", "").strip()

                result = [f"**Query:** {row.get('name', '').strip()}"]
                if description:
                    result.append(f"**Description:** {description}")
                if jql_template:
                    result.append(f"**JQL Template:** {jql_template}")
                if placeholders:
                    result.append(f"**Placeholders:** {placeholders}")
                if example:
                    result.append(f"**Example:** {example}")
                if notes:
                    result.append(f"**Notes:** {notes}")

                return "\n\n".join(result)

        # Query not found - raise error with available queries
        available = [row.get("name", "").strip() for row in sheet_data if row.get("name")]
        raise ValueError(f"Query '{query_name}' not found. Available queries: {', '.join(available)}")

    def get_slack_template(self, template_name: str) -> str:
        """Get Slack announcement template from Slack Templates sheet.

        Returns the template content which can be filled with placeholder values.
        Templates use {{PLACEHOLDER}} syntax (double curly braces).

        To discover available templates: If you don't know the template name, provide
        an invalid name (e.g., "list") and the error message will return a formatted
        list of all available template names.

        Args:
            template_name: Name of the template to retrieve (case-insensitive).

        Returns:
            Template content string with milestone, when_to_send, and data requirements.

        Raises:
            ValueError: If template_name not found. Error message includes comma-separated
                list of all available template names for easy discovery.
        """
        sheet_name = "Slack Templates"
        sheet_data = self._sheets.get(sheet_name, [])

        if not sheet_data:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

        # Search for template (case-insensitive on 'name' column - lowercase snake_case)
        template_name_lower = template_name.lower().strip()
        for row in sheet_data:
            name = row.get("name", "").strip().lower()
            if name == template_name_lower:
                template_content = row.get("template_content", "").strip()
                milestone = row.get("milestone", "").strip()
                when_to_send = row.get("when_to_send", "").strip()
                data_requirements = row.get("data_requirements", "").strip()

                result = [f"**Template:** {row.get('name', '').strip()}"]
                if milestone:
                    result.append(f"**Milestone:** {milestone}")
                if when_to_send:
                    result.append(f"**When to Send:** {when_to_send}")
                if data_requirements:
                    result.append(f"**Data Requirements:** {data_requirements}")
                result.append(f"\n**Template Content:**\n{template_content}")

                return "\n\n".join(result)

        # Template not found - raise error with available templates
        available = [row.get("name", "").strip() for row in sheet_data if row.get("name")]
        raise ValueError(f"Template '{template_name}' not found. Available templates: {', '.join(available)}")

    def get_workflow_instructions(self, action_name: str) -> str:
        """Get workflow instructions from Actions & Workflows sheet.

        Returns the complete workflow including description, required inputs,
        data sources, tools to use, output format, and step-by-step instructions.

        To discover available workflows: If you don't know the workflow name, provide
        an invalid name (e.g., "list") and the error message will return a formatted
        list of all available workflow names.

        Args:
            action_name: Name of the workflow/action to retrieve (case-insensitive).

        Returns:
            Formatted string with complete workflow details including description,
            required inputs, data sources, tools to use, output format, and step-by-step
            instructions.

        Raises:
            ValueError: If action_name not found. Error message includes comma-separated
                list of all available workflow names for easy discovery.
        """
        sheet_name = "Actions & Workflows"
        sheet_data = self._sheets.get(sheet_name, [])

        if not sheet_data:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

        # Search for workflow (case-insensitive on 'name' column - lowercase snake_case)
        action_name_lower = action_name.lower().strip()
        for row in sheet_data:
            name = row.get("name", "").strip().lower()
            if name == action_name_lower:
                description = row.get("description", "").strip()
                input_required = row.get("input_required", "").strip()
                data_sources = row.get("data_sources", "").strip()
                tools = row.get("tools", "").strip()
                output_format = row.get("output_format", "").strip()
                instructions = row.get("instructions", "").strip()

                result = [f"**Workflow:** {row.get('name', '').strip()}"]
                if description:
                    result.append(f"**Description:** {description}")
                if input_required:
                    result.append(f"**Required Input:** {input_required}")
                if data_sources:
                    result.append(f"**Data Sources:** {data_sources}")
                if tools:
                    result.append(f"**Tools:** {tools}")
                if output_format:
                    result.append(f"**Output Format:** {output_format}")
                if instructions:
                    result.append(f"**Instructions:**\n{instructions}")

                return "\n\n".join(result)

        # Workflow not found - raise error with available workflows
        available = [row.get("name", "").strip() for row in sheet_data if row.get("name")]
        raise ValueError(f"Workflow '{action_name}' not found. Available workflows: {', '.join(available)}")

    def get_project_config(self, config_key: str) -> str:
        """Get configuration value from Configuration & Setup sheet.

        To discover available config keys: If you don't know the config key name,
        provide an invalid name (e.g., "list") and the error message will return a
        formatted list of all available config keys.

        Args:
            config_key: Configuration key to retrieve (case-insensitive).
                Examples: "jira_default_base_jql", "team_mapping_gdrive_id"

        Returns:
            Formatted string with config key, value, and description.

        Raises:
            ValueError: If config_key not found. Error message includes comma-separated
                list of all available config keys for easy discovery.
        """
        sheet_name = "Configuration & Setup"
        sheet_data = self._sheets.get(sheet_name, [])

        if not sheet_data:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

        # Search for config_key (case-insensitive)
        config_key_lower = config_key.lower().strip()
        for row in sheet_data:
            key = row.get("config_key", "").strip().lower()
            if key == config_key_lower:
                value = row.get("value", "").strip()
                description = row.get("description", "").strip()

                result = [f"**Config:** {row.get('config_key', '').strip()}"]
                if value:
                    result.append(f"**Value:** {value}")
                if description:
                    result.append(f"**Description:** {description}")

                return "\n\n".join(result)

        # Config key not found - raise error with available keys
        available = [row.get("config_key", "").strip() for row in sheet_data if row.get("config_key")]
        raise ValueError(f"Config key '{config_key}' not found. Available keys: {', '.join(available)}")

    def get_tool_reference(self, tool_name: str) -> str:
        """Get tool documentation from Tools Reference sheet.

        Returns parameters, return values, usage guidance, and examples.

        To discover available tools: If you don't know the tool name, provide an
        invalid name (e.g., "list") and the error message will return a formatted
        list of all available tool names.

        Args:
            tool_name: Name of the tool to retrieve (case-insensitive).

        Returns:
            Formatted string with tool documentation including category, parameters,
            return values, usage guidance, and examples.

        Raises:
            ValueError: If tool_name not found. Error message includes comma-separated
                list of all available tool names for easy discovery.
        """
        sheet_name = "Tools Reference"
        sheet_data = self._sheets.get(sheet_name, [])

        if not sheet_data:
            raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

        # Search for tool (case-insensitive on 'Tool Name' column - Title Case)
        tool_name_lower = tool_name.lower().strip()
        for row in sheet_data:
            name = row.get("Tool Name", "").strip().lower()
            if name == tool_name_lower:
                category = row.get("Category", "").strip()
                parameters = row.get("Parameters", "").strip()
                returns = row.get("Returns", "").strip()
                use_when = row.get("Use When", "").strip()
                example = row.get("Example", "").strip()

                result = [f"**Tool:** {row.get('Tool Name', '').strip()}"]
                if category:
                    result.append(f"**Category:** {category}")
                if parameters:
                    result.append(f"**Parameters:** {parameters}")
                if returns:
                    result.append(f"**Returns:** {returns}")
                if use_when:
                    result.append(f"**Use When:** {use_when}")
                if example:
                    result.append(f"**Example:** {example}")

                return "\n\n".join(result)

        # Tool not found - raise error with available tools
        available = [row.get("Tool Name", "").strip() for row in sheet_data if row.get("Tool Name")]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {', '.join(available)}")

    # NOTE: get_response_format() removed - "Response Formats" sheet replaced by "Prompts" sheet
    # Use get_prompt() instead for situational guidance

    def _validate_workbook_schema(self, sheets_data: dict[str, list[dict[str, str]]]) -> None:
        """Validate that workbook contains required sheets and columns.

        Args:
            sheets_data: Dictionary mapping sheet names to list of row dicts.

        Raises:
            ValueError: If required sheets or columns are missing.
        """
        errors = []

        # Check each required sheet
        for sheet_name, schema in SHEET_SCHEMA.items():
            if sheet_name not in sheets_data:
                errors.append(f"❌ Missing required sheet: '{sheet_name}'")
                continue

            # Get sheet data
            sheet_rows = sheets_data[sheet_name]
            if not sheet_rows:
                errors.append(f"⚠️  Sheet '{sheet_name}' is empty (no data rows)")
                continue

            # Check columns by examining first row
            actual_columns = set(sheet_rows[0].keys())
            required_columns = set(schema["required"])
            missing_columns = required_columns - actual_columns

            if missing_columns:
                errors.append(
                    f"❌ Sheet '{sheet_name}' missing required columns: {sorted(missing_columns)}\n"
                    f"   Found columns: {sorted(actual_columns)}\n"
                    f"   Required: {sorted(required_columns)}"
                )

        # If errors found, raise with detailed message
        if errors:
            available_sheets = sorted(sheets_data.keys())
            error_msg = [
                "Workbook validation failed:",
                "",
                *errors,
                "",
                f"Available sheets in workbook: {available_sheets}",
                "",
                "Expected schema:",
            ]

            for sheet_name, schema in SHEET_SCHEMA.items():
                error_msg.append(f"  • {sheet_name}:")
                error_msg.append(f"    - Required columns: {schema['required']}")
                error_msg.append(f"    - Optional columns: {schema['optional']}")

            raise ValueError("\n".join(error_msg))

    # Helper methods for system prompt (NOT registered as tools)
    def list_available_queries(self) -> list[str]:
        """List all available Jira query names.

        Returns:
            List of query names from 'name' column.
        """
        sheet_data = self._sheets.get("Jira Queries", [])
        return [row.get("name", "").strip() for row in sheet_data if row.get("name")]

    def list_available_templates(self) -> list[str]:
        """List all available Slack template names.

        Returns:
            List of template names from 'name' column.
        """
        sheet_data = self._sheets.get("Slack Templates", [])
        return [row.get("name", "").strip() for row in sheet_data if row.get("name")]

    def list_available_workflows(self) -> list[str]:
        """List all available workflow names.

        Returns:
            List of workflow names from 'name' column.
        """
        sheet_data = self._sheets.get("Actions & Workflows", [])
        return [row.get("name", "").strip() for row in sheet_data if row.get("name")]

    def list_queries_with_descriptions(self) -> list[tuple[str, str, str]]:
        """List all Jira queries with their descriptions and trigger phrases.

        Returns:
            List of (name, description, trigger_phrases) tuples.
            trigger_phrases is empty string if not present.
        """
        sheet_data = self._sheets.get("Jira Queries", [])
        return [
            (row.get("name", "").strip(), row.get("description", "").strip(), row.get("trigger_phrases", "").strip())
            for row in sheet_data
            if row.get("name")
        ]

    def list_templates_with_descriptions(self) -> list[tuple[str, str, str]]:
        """List all Slack templates with their when_to_send descriptions and trigger phrases.

        Returns:
            List of (name, when_to_send, trigger_phrases) tuples.
            trigger_phrases is empty string if not present.
        """
        sheet_data = self._sheets.get("Slack Templates", [])
        return [
            (row.get("name", "").strip(), row.get("when_to_send", "").strip(), row.get("trigger_phrases", "").strip())
            for row in sheet_data
            if row.get("name")
        ]

    def list_workflows_with_descriptions(self) -> list[tuple[str, str, str]]:
        """List all workflows with their descriptions and trigger phrases.

        Returns:
            List of (name, description, trigger_phrases) tuples.
            trigger_phrases is empty string if not present.
        """
        sheet_data = self._sheets.get("Actions & Workflows", [])
        return [
            (row.get("name", "").strip(), row.get("description", "").strip(), row.get("trigger_phrases", "").strip())
            for row in sheet_data
            if row.get("name")
        ]

    def get_system_prompt(self) -> str:
        """Get system prompt from Prompts sheet (internal use by configurator).

        Returns:
            System prompt content (prompt_type='system')

        Raises:
            ValueError: If no system prompt found
        """
        sheet_data = self._sheets.get("Prompts", [])
        if not sheet_data:
            raise ValueError("Prompts sheet not found in workbook")

        # Find row with prompt_type = 'system'
        for row in sheet_data:
            if row.get("prompt_type", "").strip().lower() == "system":
                return row.get("prompt_content", "").strip()

        raise ValueError("No system prompt found. Expected row with prompt_type='system'")

    def get_prompt(self, prompt_name: str) -> str:
        """Get situational prompt by name (exposed as agent tool).

        Provides detailed guidance for specific situations like risk identification,
        team coordination, or release readiness assessment.

        To discover available prompts: If you don't know the prompt name, provide an
        invalid name (e.g., "list") and the error message will return a formatted list
        of all available situational prompts.

        Args:
            prompt_name: Name of prompt (case-insensitive)

        Returns:
            Formatted prompt with context and content for the specific situation

        Raises:
            ValueError: If prompt not found. Error message includes comma-separated
                list of all available prompt names for easy discovery.
        """
        sheet_data = self._sheets.get("Prompts", [])
        if not sheet_data:
            raise ValueError("Prompts sheet not found in workbook")

        prompt_name_lower = prompt_name.strip().lower()

        # Search situational prompts only (exclude system)
        for row in sheet_data:
            if row.get("prompt_type", "").strip().lower() == "system":
                continue  # Skip system prompt

            if row.get("name", "").strip().lower() == prompt_name_lower:
                context = row.get("context", "").strip()
                content = row.get("prompt_content", "").strip()

                if context:
                    return f"**Context**: {context}\n\n{content}"
                return content

        # Not found - list available
        available = self.list_available_prompts()
        raise ValueError(f"Prompt '{prompt_name}' not found. Available prompts: {', '.join(available)}")

    def list_available_prompts(self) -> list[str]:
        """List situational prompt names (excludes system prompt).

        Returns:
            Sorted list of prompt names
        """
        sheet_data = self._sheets.get("Prompts", [])
        if not sheet_data:
            return []

        names = []
        for row in sheet_data:
            if row.get("prompt_type", "").strip().lower() != "system":
                name = row.get("name", "").strip()
                if name:
                    names.append(name)

        return sorted(names)

    def list_prompts_with_descriptions(self) -> list[tuple[str, str]]:
        """List situational prompts with descriptions (for system prompt reference).

        Returns:
            List of (name, description) tuples (excludes system prompt)
        """
        sheet_data = self._sheets.get("Prompts", [])
        if not sheet_data:
            return []

        prompts = []
        for row in sheet_data:
            if row.get("prompt_type", "").strip().lower() != "system":
                name = row.get("name", "").strip()
                desc = row.get("description", "").strip()
                if name:
                    prompts.append((name, desc))

        return prompts

    def has_trigger_phrases(self, sheet_name: str) -> bool:
        """Check if any row in the sheet has trigger_phrases data.

        Args:
            sheet_name: Name of the sheet to check.

        Returns:
            True if at least one row has non-empty trigger_phrases.
        """
        sheet_data = self._sheets.get(sheet_name, [])
        for row in sheet_data:
            if row.get("trigger_phrases", "").strip():
                return True
        return False

    def get_all_config_values(self) -> dict[str, str]:
        """Get all configuration values as a dictionary (for system prompt injection).

        Returns:
            Dictionary mapping config_key to value.
        """
        sheet_data = self._sheets.get("Configuration & Setup", [])
        if not sheet_data:
            return {}

        config = {}
        for row in sheet_data:
            key = row.get("config_key", "").strip()
            value = row.get("value", "").strip()
            if key and value:
                config[key] = value

        return config

    def get_all_config_values_with_descriptions(self) -> list[tuple[str, str, str]]:
        """Get all configuration values with descriptions (for system prompt injection).

        Returns:
            List of (config_key, value, description) tuples. Description may be empty string.
        """
        sheet_data = self._sheets.get("Configuration & Setup", [])
        if not sheet_data:
            return []

        configs = []
        for row in sheet_data:
            key = row.get("config_key", "").strip()
            value = row.get("value", "").strip()
            description = row.get("description", "").strip()
            if key and value:
                configs.append((key, value, description))

        return configs
