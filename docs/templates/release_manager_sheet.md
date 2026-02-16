# Release Manager Excel Workbook Generation Prompt

## Purpose

Generate a comprehensive Excel workbook from the Release Manager system prompt and maintenance guide. This workbook serves as a structured reference for Release Managers, making it easier to:

- Look up Jira queries
- Find workflow instructions
- Access Slack templates
- Review tool documentation
- Follow best practices
- Access situation-specific prompts

## Source Documents

- `docs/templates/release_manager_system_prompt.md` - Extended system prompt with queries, actions, and templates
- `docs/templates/release_manager_prompt_guide.md` - Maintenance guide with best practices

## Placeholder Syntax

**All templates use double curly brace notation: `{{PLACEHOLDER}}`**

This syntax is used throughout the workbook for all placeholder values (release versions, issue counts, dates, etc.):
- `{{RELEASE_VERSION}}` - Release version (e.g., "1.9.0")
- `{{ISSUE_TYPE}}` - Jira issue type (e.g., "Bug", "Feature")
- `{{ISSUE_COUNT}}` - Number of issues
- `{{JIRA_LINK}}` - Jira search URL
- `{{TEAM_NAME}}` - Team name
- `{{FEATURE_FREEZE_DATE}}` - Freeze date
- etc.

**Why `{{...}}` syntax?**
- No conflicts with markdown links `[text](url)`
- Industry standard (Mustache, Handlebars, Jinja2)
- Visually distinctive and easy to find-and-replace
- Works in JQL queries, Slack templates, and documentation

## Workbook Structure

Create an Excel workbook with **7 sheets** in the following order:

**Configuration (Machine-Readable)**
1. Configuration & Setup

**Maintenance & Reference (Informational)**
2. Maintenance Guide
3. Tools Reference (includes Response Formats)

**Operational (Machine-Readable)**
4. Prompts
5. Jira Queries
6. Actions & Workflows
7. Slack Templates

---

## Sheet 1: Configuration & Setup

**Purpose:** Machine-readable configuration values used by the Release Manager agent code

**Note:** This is a machine-readable sheet. Column headers use lowercase snake_case to match Python variable conventions.

**Columns:**
| config_key | value | description |
|------------|-------|-------------|

**Data to Include:**

ONLY configuration values that are:
1. Actually referenced in workflows or code
2. Make sense to configure (not hardcoded constants)
3. Provide operational value

**Current Configuration Values:**

**Jira Configuration:**
- `jira_default_base_jql`: Default JQL scope for Release Manager queries
  - Value: `project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND status != closed`
  - Used in: Jira toolkit configuration for scoping all queries

**Jira Project Keys:**
- `jira_project_rhdhplan`: RHDHPLAN project key
  - Value: `RHDHPLAN`
  - Description: Track outcome, features and feature requests for strategic planning

- `jira_project_rhidp`: RHIDP project key
  - Value: `RHIDP`
  - Description: Engineering jira project - tracks EPICs, Story, Task, sub-tasks

- `jira_project_rhdh_bugs`: RHDHBugs project key
  - Value: `RHDHBugs`
  - Description: Tracks product bugs with bug type

- `jira_project_rhdh_supp`: RHDHSUPP project key
  - Value: `RHDHSUPP`
  - Description: Tracks support interactions with customers as bug type

**External Resources:**
- `team_mapping_gdrive_id`: Google Drive file ID for RHDH Team Mapping spreadsheet
  - Value: `1Dv1JWsQe3Ew82WLFQNhyAwqsn9oEkh2MjoKyHXPuJkk`
  - Used in: "Retrieve Teams and Leads" workflow

- `release_schedule_gdrive_id`: Google Drive file ID for Release Schedule spreadsheet
  - Value: `1knVzlMW0l0X4c7gkoiuaGql1zuFgEGwHHBsj-ygUTnc`
  - Used in: "Retrieving Future Release and Key Dates" workflow

**Formatting:**
- Bold headers (lowercase snake_case)
- Filter enabled on all columns
- Freeze first row
- Wrap text in all columns
- Wide columns for `value` (80 chars) and `description` (60 chars)
- Auto-fit row heights

**Design Principles:**
1. **Configuration, not documentation**: Only values that configure agent behavior
2. **Referenced, not invented**: Only values actually used in workflows/code
3. **Programmatically accessible**: Values are injected into system prompt via `ReleaseManagerToolkit.get_all_config_values()`

**How Config Values are Used:**
Configuration values are automatically injected into the agent's system prompt through the `_build_config_section()` method in `release_manager_configurator.py`. This makes them available to the agent at runtime without hardcoding.

---

## Sheet 2: Maintenance Guide

**Purpose:** Best practices, troubleshooting, and prompt engineering principles

**Columns:**
| Category | Topic | Guideline/Issue | Recommendation/Solution | Example | Reference |
|----------|-------|-----------------|-------------------------|---------|-----------|

**Data to Include:**

From `release_manager_prompt_guide.md`, extract key sections:

**Category: "Prompt Engineering Principles"**
Extract from "Prompt Engineering Best Practices" section:
- Principle 1: Explicit Tool Mapping
- Principle 2: DRY (Don't Repeat Yourself)
- Principle 3: Conciseness - Assume the LLM is Smart
- Principle 4: Outcome-Focused Instructions
- Principle 5: Format Targeting (Destination + Delivery Method)

For each principle:
- Topic: Principle name
- Guideline/Issue: The "Problem" description
- Recommendation/Solution: The "Good" approach and "Why" explanation
- Example: Code examples from the principle
- Reference: "Prompt Engineering Best Practices"

**Category: "Common Pitfalls"**
Extract from "Common Pitfalls to Avoid":
- Empty Section Placeholders
- Mixing Formatting Syntaxes
- Triple-Duplicated Queries
- Meta-Commentary About Thinking
- Abstract Action Names Without Tool Mapping

**Category: "Troubleshooting"**
Extract from "Troubleshooting" section:
- Agent Not Using My Instructions
- Document Permission Issues
- Changes Not Appearing

For each issue:
- Topic: Issue name
- Guideline/Issue: Symptom description
- Recommendation/Solution: "What You Can Do" steps
- Example: Specific examples if provided

**Category: "Best Practices"**
Extract from "Best Practices" section:
- Writing Effective Instructions
- Maintenance Schedule

**Category: "Google Docs Formatting"**
Extract key formatting conversion rules from "Formatting Your Prompt in Google Docs"

**Formatting:**
- Bold headers
- Filter enabled on all columns
- Freeze first row
- Wrap text in all columns
- Group rows by Category (Excel grouping feature)
- Alternating colors by Category
- Wide columns for Recommendation/Solution and Example

---

## Sheet 3: Tools Reference

**Purpose:** Documentation of available tools and response formats

**Columns:**
| Tool Name | Category | Parameters | Returns | Use When | Response Format | Example |
|-----------|----------|------------|---------|----------|-----------------|---------|

**Data Extraction Strategy:**

**IMPORTANT: Use the Task tool with subagent_type="Explore" to discover available toolkits dynamically.**

Before extracting tool data from source documents, launch an Explore agent to examine the actual toolkit implementations:

```
Task: Explore agent to examine Release Manager toolkits
Prompt: "Examine the ReleaseManagerToolkit and related toolkit classes in src/agentllm/tools/ to identify all available tool methods. For each tool method, extract:
- Tool name (method name)
- Category (Jira, Google Drive, Release Manager, etc.)
- Parameters with defaults
- Return type/description
- **'Use When' guidance from docstring** (look for '**Use When:**' section)
- **'DO NOT Use For' anti-patterns** (look for '**DO NOT Use For:**' section)
- Example usage

Focus on:
- src/agentllm/tools/release_manager_toolkit.py
- src/agentllm/tools/jira_toolkit.py
- src/agentllm/tools/gdrive_utils.py
- Any other toolkit files referenced in the codebase

**Key Pattern to Document:**
All Jira tools follow a standardized docstring format with 'Use When' and 'DO NOT Use For' sections at the top. These are dynamically extracted by JiraConfig._extract_tool_use_when() to build the Tool Selection Guide in the agent's system prompt. This ensures single source of truth - docstrings drive both documentation and runtime behavior.

Return a structured list of all discovered tools."
```

After receiving the Explore agent results, supplement with data from source documents if needed.

**Expected Tools:**
- Release Manager tools: `get_jira_query_template()`, `get_slack_template()`, `get_workflow_instructions()`, etc.
- Jira tools: `get_issue()`, `get_issues_summary()`, `get_issues_detailed()`, `get_issues_stats()`, `get_issues_by_team()`, etc.
- Google Drive tools: `get_document_content()`, `get_user_info()`

For each tool, populate:
- **Tool Name**: Function name
- **Category**: "Release Manager", "Jira", or "Google Drive"
- **Parameters**: Parameter list with defaults
- **Returns**: What the tool returns
- **Use When**: Extract from the `**Use When:**` section in tool docstring (first bullet point recommended for conciseness). For Jira tools, also note any `**DO NOT Use For:**` anti-patterns.
- **Response Format**: Link to applicable response format (see below)
- **Example**: Simple example call

**DRY Principle Note:**
The "Use When" guidance documented here should match what's in the tool docstrings, as that's the single source of truth. The agent's system prompt is built dynamically by extracting these docstrings at runtime (see `JiraConfig._extract_tool_use_when()` and `get_agent_instructions()`).

**Response Formats Section:**

Add response format rows after the tools. From "Response standards and formats" section:

1. **Detailed format**
   - Tool Name: "(Response Format)"
   - Category: "Output Format"
   - Use When: When detailed issue information is needed
   - Response Format: Total count, Jira Key/Summary (linked), Status, Priority, Assignee, Jira search link
   - Example: Bullet list with all elements

2. **Summary format**
   - Tool Name: "(Response Format)"
   - Category: "Output Format"
   - Use When: When only count is needed
   - Response Format: Total count, Jira search link

3. **Summary by Team**
   - Tool Name: "(Response Format)"
   - Category: "Output Format"
   - Use When: Team-level aggregation
   - Response Format: Table with Team Name, Total Issues, Jira Search Link (per team)

4. **Detailed by Team**
   - Tool Name: "(Response Format)"
   - Category: "Output Format"
   - Use When: Team breakdown by issue type
   - Response Format: Table with Team Name, Breakdown by type (Features, Epics, Stories, Tasks, Bugs), Links for each type

**Formatting:**
- Bold headers
- Filter enabled
- Freeze first row
- Wrap text in "Use When" and "Response Format" columns
- Auto-fit columns
- Group rows: Tools first, then Response Formats section with visual separator

---

## Sheet 4: Prompts

**Purpose:** Situation-specific prompts and system prompt for the Release Manager agent

**Note:** This is a machine-readable sheet. Column headers use lowercase snake_case to match agent skill frontmatter conventions.

**Columns:**
| name | description | prompt_type | context | prompt_content |
|------|-------------|-------------|---------|----------------|

**Data to Include:**

**System Prompt:**
- **name**: "system_prompt"
- **description**: "Core system prompt for Release Manager agent"
- **prompt_type**: "system"
- **context**: "Always active - defines agent identity and core capabilities"
- **prompt_content**: Extract from the "Core Principles" and introductory sections of `release_manager_system_prompt.md`. Include:
  - Agent identity ("You are the Release Manager for Red Hat Developer Hub...")
  - Core responsibilities
  - Key principles (accuracy, traceability, actionable recommendations)
  - Available tools summary
  - General guidance

**Situational Prompts:**

Create situational prompts for common scenarios. Extract from source documents or infer from workflows:

1. **Feature Freeze Preparation**
   - **name**: "feature_freeze_prep"
   - **description**: "Guidance for preparing Feature Freeze announcement"
   - **prompt_type**: "situational"
   - **context**: "Use when user asks to prepare for Feature Freeze"
   - **prompt_content**: "When preparing Feature Freeze announcements: (1) Verify freeze date from release issue, (2) Gather team issue counts using get_issues_by_team(), (3) Identify outstanding release notes, (4) Check for blockers or risks, (5) Use Slack template with all placeholders filled."

2. **Code Freeze Preparation**
   - **name**: "code_freeze_prep"
   - **description**: "Guidance for preparing Code Freeze announcement"
   - **prompt_type**: "situational"
   - **context**: "Use when user asks to prepare for Code Freeze"
   - **prompt_content**: Similar structure to Feature Freeze

3. **Release Status Check**
   - **name**: "release_status_check"
   - **description**: "How to provide comprehensive release status"
   - **prompt_type**: "situational"
   - **context**: "Use when user asks for release status or progress"
   - **prompt_content**: "For release status: (1) Query open issues by type, (2) Identify blockers and CVEs, (3) Check epic status, (4) Review outstanding release notes, (5) Provide completion percentage, (6) Highlight risks."

4. **Risk Identification**
   - **name**: "risk_identification"
   - **description**: "How to identify and communicate release risks"
   - **prompt_type**: "situational"
   - **context**: "Use when analyzing release health or identifying problems"
   - **prompt_content**: "Risk indicators: (1) Blocker bugs near freeze dates, (2) High open issue count per team, (3) Missing release notes, (4) Critical CVEs, (5) Epics not in Dev Complete. Always provide actionable recommendations."

5. **Team Coordination**
   - **name**: "team_coordination"
   - **description**: "How to coordinate information across teams"
   - **prompt_type**: "situational"
   - **context**: "Use when generating team-specific updates or breakdowns"
   - **prompt_content**: "For team coordination: (1) Use get_issues_by_team() for accurate counts (never manual counting!), (2) Include team leads' Slack handles, (3) Provide Jira links for each team, (4) Highlight teams at risk, (5) Suggest follow-up actions."

**Formatting:**
- Bold headers (lowercase snake_case)
- Filter enabled
- Freeze first row
- Wrap text enabled for all columns
- Wide `prompt_content` column (at least 100 characters wide)
- Tall row heights for prompt rows
- System prompt row should be visually distinct (e.g., light yellow background)

---

## Sheet 5: Jira Queries

**Purpose:** Reusable JQL query templates with placeholders

**Note:** This is a machine-readable sheet. Column headers use lowercase snake_case to match agent skill frontmatter conventions.

**Columns:**
| name | description | jql_template | placeholders | example | notes |
|------|-------------|--------------|--------------|---------|-------|

**Data to Include:**

From "Jira Query" section, extract all query subsections:

1. active_release
2. open_issues
3. open_issues_by_type
4. epics
5. cves
6. feature_demos
7. feature_subtasks
8. test_day_features
9. features_added_to_release
10. release_notes
11. feature_freeze_issues
12. code_freeze_issues

For each query:
- **name**: Optimized snake_case name (e.g., "active_release")
- **description**: What this query retrieves
- **jql_template**: The actual JQL (convert to {{RELEASE_VERSION}} and {{ISSUE_TYPE}} placeholders)
- **placeholders**: {{RELEASE_VERSION}} or {{ISSUE_TYPE}} or both (comma-separated if multiple)
- **example**: Replace placeholder with real example (e.g., "1.9.0")
- **notes**: Any special instructions

**Important Transformations:**
- When extracting JQL templates from source documents, replace any `[PLACEHOLDER]` bracket notation with `{{PLACEHOLDER}}` curly brace notation
- Optimize query names: Remove redundant prefixes like "jira list of" or "Jira list of" and convert to snake_case (e.g., "jira list of active release" → "active_release")

**Formatting:**
- Bold headers (lowercase snake_case)
- Filter enabled
- Freeze first row
- Monospace font for `jql_template` column
- Wrap text in `description` and `notes` columns
- Wide columns for `jql_template` (at least 80 characters)

---

## Sheet 6: Actions & Workflows

**Purpose:** Step-by-step instructions for each retrieval action

**Note:** This is a machine-readable sheet. Column headers use lowercase snake_case to match agent skill frontmatter conventions.

**Columns:**
| name | description | input_required | data_sources | tools | output_format | instructions |
|------|-------------|----------------|--------------|-------|---------------|--------------|

**Data to Include:**

From "Actions" section, extract each action subsection:

1. Retrieving Release and Key Dates
2. Retrieving Future Release and Key Dates
3. Retrieve Active Release Status by Issue Type
4. Recognize release versions
5. Retrieve Teams and Leads
6. Retrieve Issues by Engineering Teams
7. Retrieve Blocker Bugs
8. Retrieve Engineering EPICs
9. Retrieve list of CVEs
10. Retrieve list of open issues for release
11. Retrieve Feature Demos
12. Retrieve Feature Subtasks
13. Retrieve Test Day Features
14. Retrieve new features added to a Release
15. Retrieve outstanding Release Notes
16. Announce Feature Freeze Update
17. Announce Feature Freeze
18. Announce Code Freeze Update
19. Announce Code Freeze

For each action:
- **name**: Section heading (e.g., "Retrieving Release and Key Dates")
- **description**: From "Objective:" or "Output:" line
- **input_required**: Target release version, team ID, etc.
- **data_sources**: Jira, Google Drive doc, etc.
- **tools**: Specific tool function names mentioned (e.g., `get_issue()`, `get_issues_summary()`)
- **output_format**: Reference to response format (Detailed, Summary, etc.)
- **instructions**: Condensed version of step-by-step instructions

**Formatting:**
- Bold headers (lowercase snake_case)
- Filter enabled
- Freeze first row
- Wrap text in all columns
- Alternating row colors for readability

---

## Sheet 7: Slack Templates

**Purpose:** Announcement templates for freeze milestones (copy-paste ready)

**Note:** This is a machine-readable sheet. Column headers use lowercase snake_case to match agent skill frontmatter conventions.

**Columns:**
| name | milestone | when_to_send | data_requirements | template_content |
|------|-----------|--------------|-------------------|------------------|

**Data to Include:**

From "Actions" section, extract announcement subsections:

1. **Announce Feature Freeze Update**
   - **name**: "Feature Freeze Update"
   - **milestone**: "Feature Freeze"
   - **when_to_send**: "Before Feature Freeze date"
   - **data_requirements**: List all from "Data Requirements" section
   - **template_content**: Full Slack Markdown template from triple backticks

2. **Announce Feature Freeze**
   - **name**: "Feature Freeze Announcement"
   - **milestone**: "Feature Freeze"
   - **when_to_send**: "On Feature Freeze date"
   - **data_requirements**: List all requirements
   - **template_content**: Full template

3. **Announce Code Freeze Update**
   - **name**: "Code Freeze Update"
   - **milestone**: "Code Freeze"
   - **when_to_send**: "Before Code Freeze date"
   - **data_requirements**: List all requirements
   - **template_content**: Full template

4. **Announce Code Freeze**
   - **name**: "Code Freeze Announcement"
   - **milestone**: "Code Freeze"
   - **when_to_send**: "On Code Freeze date"
   - **data_requirements**: List all requirements
   - **template_content**: Full template

**Special Instructions:**
- Keep template content EXACTLY as written (preserve Markdown syntax, emojis, formatting)
- Use line breaks in cells to preserve template structure
- Do NOT convert Markdown to Excel formatting
- Templates are meant to be copied and pasted into Slack
- **Convert all `[PLACEHOLDER]` bracket notation to `{{PLACEHOLDER}}` curly brace notation** in template content

**Formatting:**
- Bold headers (lowercase snake_case)
- Filter enabled
- Freeze first row
- Wrap text enabled for all columns
- Wide `template_content` column (at least 100 characters wide)
- Monospace font for `template_content` column
- Tall row heights for template rows

---

## General Formatting Guidelines

Apply to ALL sheets:

1. **Header Row:**
   - Bold text
   - Background color: Light blue (#4472C4)
   - Font color: White
   - Freeze panes (row 1)
   - Enable filters

2. **Column Widths:**
   - Auto-fit based on content
   - Minimum width: 15 characters
   - Maximum width: 100 characters (except template/prompt columns)

3. **Text Wrapping:**
   - Enable on all cells
   - Auto-fit row heights

4. **Fonts:**
   - Headers: Calibri 11pt Bold
   - Body: Calibri 11pt Regular
   - Code/Templates/Prompts: Consolas 10pt (for JQL queries, tool names, templates, prompt content)

5. **Borders:**
   - All cells have light gray borders

6. **Protection:**
   - Protect all sheets (no password)
   - Allow filtering and sorting

7. **Tab Colors:**
   - Configuration sheet (1): Light green (machine-readable)
   - Maintenance & Reference sheets (2-3): Light blue
   - Operational sheets (4-7): Light green (machine-readable)

---

## Output File

**Filename:** `RHDH_Release_Manager_Reference.xlsx`

**Sheet Order (MUST follow this exactly):**
1. Configuration & Setup
2. Maintenance Guide
3. Tools Reference
4. Prompts
5. Jira Queries
6. Actions & Workflows
7. Slack Templates

---

## Validation

After generating the workbook, verify:

- [ ] All 7 sheets present in correct order
- [ ] All sheets have frozen header rows
- [ ] All sheets have filters enabled
- [ ] Tab colors applied correctly
- [ ] Jira Queries sheet has all 12+ queries
- [ ] Slack Templates sheet has all 4 templates with preserved formatting
- [ ] Prompts sheet has system_prompt + 5 situational prompts
- [ ] Tools Reference sheet includes tools (from Explore agent) + response formats
- [ ] No empty cells in critical columns (`name`, `description`, etc.)
- [ ] Text wrapping enabled where needed
- [ ] Monospace font applied to code/template/prompt columns
- [ ] Machine-readable sheets (4-7) use lowercase snake_case headers
- [ ] Informational sheets (1-3) use Title Case headers

---

## Usage Instructions

To generate the workbook:

1. Use the `document-skills:xlsx` skill
2. Reference this prompt document
3. **Launch Explore agent** to discover available toolkit methods (see Sheet 3 instructions)
4. Read source documents:
   - `docs/templates/release_manager_system_prompt.md`
   - `docs/templates/release_manager_prompt_guide.md`
5. Generate the Excel file according to specifications above
6. Save as `RHDH_Release_Manager_Reference.xlsx`

**Example command:**
```
Please create an Excel workbook following the specifications in docs/templates/release_manager_sheet.md
```
