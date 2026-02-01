# Using the Release Manager Excel Workbook - AI Agent Guide

## Purpose

This guide explains how AI agents should use the Release Manager Excel workbook (`RHDH_Release_Manager_Reference.xlsx`) as a structured knowledge base for Release Manager tasks.

**Key Principle:** The Excel workbook is a **queryable reference**, not a replacement for the system prompt. Use it to look up specific queries, templates, and workflows efficiently.

---

## Workbook Overview

The workbook contains 7 sheets organized into two categories:

**Maintenance & Reference (Informational)**
1. Maintenance Guide
2. Configuration & Setup
3. Tools Reference (includes Response Formats)

**Operational (Machine-Readable)**
4. Prompts
5. Jira Queries
6. Actions & Workflows
7. Slack Templates

**Note on Machine-Readable Sheets:**
- Sheets 4-7 (Prompts, Jira Queries, Actions & Workflows, Slack Templates) use **lowercase snake_case** column headers
- This matches agent skill frontmatter conventions: `name`, `description`, `input_required`, `prompt_content`, etc.
- Sheets 1-3 use traditional Title Case for human readability

---

## Placeholder Syntax

**All templates use double curly brace notation: `{{PLACEHOLDER}}`**

Throughout the workbook, you'll encounter placeholders that need to be replaced with actual values:
- `{{RELEASE_VERSION}}` - Release version (e.g., "1.9.0")
- `{{ISSUE_TYPE}}` - Jira issue type (e.g., "Bug", "Feature")
- `{{ISSUE_COUNT}}` - Number of issues
- `{{JIRA_LINK}}` - Jira search URL
- `{{TEAM_NAME}}` - Team name
- `{{FEATURE_FREEZE_DATE}}` - Freeze date
- `{{LEAD_SLACK}}` - Slack handle

**Why `{{...}}` syntax?**
- No conflicts with markdown links `[text](url)`
- Industry standard (Mustache, Handlebars, Jinja2)
- Easy to find and replace programmatically
- Visually distinctive

**Critical:** Always replace ALL placeholders with actual values before returning output to users. Never leave `{{PLACEHOLDER}}` notation in final responses.

---

## When to Use the Workbook

### ✅ DO Use the Workbook When:

**1. User asks for specific Jira data:**
```
User: "Show me all open bugs for release 1.9.0"
→ Check Sheet 5 (Jira Queries) for "jira list of open issues by type query template"
→ Replace {{RELEASE_VERSION}} with "1.9.0" and {{ISSUE_TYPE}} with "Bug"
→ Execute query using get_issues_summary()
```

**2. User requests a status update or announcement:**
```
User: "Create Feature Freeze update for 1.9.0"
→ Check Sheet 7 (Slack Templates) for "Feature Freeze Update"
→ Review "Data Requirements" column
→ Gather required data using tools from Sheet 3
→ Fill template with actual data
→ Return formatted message
```

**3. You need to understand which tool to use:**
```
Task: Get team-level issue counts
→ Check Sheet 3 (Tools Reference)
→ Find get_issues_by_team() in "Tool Name" column
→ Read "Use When" column: "Need per-team breakdowns"
→ Check "Parameters" column for required inputs
→ Execute tool call
```

**4. You need to format output:**
```
Task: Present blocker bugs to user
→ Check Sheet 3 (Tools Reference, Category="Output Format")
→ Find "Detailed" format
→ Read "Response Format": Total count, Jira Key/Summary (linked), Status, Priority, Assignee
→ Format output accordingly
```

**5. You're unsure about workflow steps:**
```
User: "What are the outstanding release notes?"
→ Check Sheet 6 (Actions & Workflows)
→ Find "Retrieve outstanding Release Notes"
→ Read "Tools to Use" column: get_issues_summary()
→ Read "Instructions Summary" for steps
→ Execute workflow
```

### ❌ DO NOT Use the Workbook When:

**1. Making simple conversational responses:**
```
User: "Hello"
→ Just respond naturally, no workbook lookup needed
```

**2. Information is already in your context:**
```
User: "What tools do you have?"
→ You already know your tools, describe them conversationally
→ Only reference Sheet 3 if user asks for detailed parameter specs
```

**3. User asks for strategic advice:**
```
User: "Should we delay the release?"
→ Use reasoning and context, not workbook lookup
```

---

## How to Query Each Sheet

### Sheet 1: Maintenance Guide

**Use for:** Understanding prompt engineering best practices (internal reference)

**Query Pattern:**
1. This sheet is primarily for prompt maintainers, not runtime queries
2. Reference if you encounter ambiguous instructions in the system prompt
3. Check troubleshooting section if you get errors accessing data sources
4. Review prompt engineering principles when designing new workflows

**Example:**
```
Issue: System prompt has duplicate query definitions
→ Check Sheet 1, Category = "Common Pitfalls"
→ Find "Triple-Duplicated Queries"
→ Understand this is a prompt maintenance issue, not a runtime issue
→ Continue with best available query
```

**When to Reference:**
- Encountering errors or unexpected agent behavior
- Need guidance on prompt structure best practices
- Troubleshooting data access issues
- Understanding design patterns for Release Manager

---

### Sheet 2: Configuration & Setup

**Use for:** Understanding project structure, core principles, version format

**Query Pattern:**
1. Read the sheet to understand Jira project keys (RHDHPlan, RHIDP, RHDHBugs, RHDHSupp)
2. Reference when constructing cross-project JQL queries
3. Check version format rules when validating user input

**Example:**
```
User: "What's the difference between RHIDP and RHDHBugs?"
→ Look up both in Sheet 2, "Category" = "Jira Projects"
→ Return descriptions from "Description" column
```

---

### Sheet 3: Tools Reference

**Use for:** Tool selection, parameter lookup, understanding tool capabilities, and response formatting

**Note:** This sheet includes both tool documentation AND response format specifications.

**Query Pattern:**
1. **For Tools:** Filter by "Category" (Release Manager, Jira, Google Drive, or Output Format)
2. Search "Use When" column for your current task
3. Read "Parameters" and "Returns" columns for implementation details
4. **For Response Formats:** Look up format in Category = "Output Format"
5. Check "Example" column for usage patterns

**Example - Finding a Tool:**
```
Task: Need to get issue statistics breakdown
→ Filter "Tool Name" column for "stats" keyword
→ Find get_issues_stats()
→ Read "Returns": "count statistics and breakdowns (by type, status, priority)"
→ Read "Parameters": jql_query, max_results=50
→ Execute: get_issues_stats("project = RHIDP AND fixVersion = '1.9.0'")
```

**Example - Finding Response Format:**
```
Task: Show blocker bugs with full details
→ Filter Category = "Output Format"
→ Find "Detailed" format
→ Read "Response Format": Total count, Jira Key/Summary (linked), Status, Priority, Assignee, Jira search link
→ Structure output with all elements
```

**Tool Selection Decision Tree:**
```
Need counts only?
  → get_issues_stats() or get_issues_by_team()

Need to display issues to user?
  → get_issues_summary() (basic) or get_issues_detailed() (with custom fields)

Need per-team breakdown?
  → get_issues_by_team() (not manual counting!)

Need single issue details?
  → get_issue()

Need query templates?
  → get_jira_query_template()

Need Slack templates?
  → get_slack_template()

Need workflow instructions?
  → get_workflow_instructions()
```

**Response Format Selection:**
- User wants counts only → "Summary"
- User wants issue details → "Detailed"
- User wants team comparison → "Summary by Team"
- User wants team details by type → "Detailed by Team"

---

### Sheet 4: Prompts

**Use for:** Accessing situation-specific prompts and system prompt

**Note:** This is a machine-readable sheet using lowercase snake_case headers: `name`, `description`, `prompt_type`, `context`, `prompt_content`

**Query Pattern:**
1. Identify the situation type (system, feature_freeze_prep, code_freeze_prep, release_status_check, risk_identification, team_coordination)
2. Look up prompt in `name` column
3. Read `context` to confirm applicability
4. Apply `prompt_content` guidance to current task

**Example:**
```
User: "Prepare Feature Freeze announcement for 1.9.0"
→ Search Sheet 4 `name` column for "feature_freeze"
→ Find "feature_freeze_prep"
→ Read `prompt_content`: "When preparing Feature Freeze announcements: (1) Verify freeze date...(2) Gather team issue counts...(3) Identify outstanding release notes...(4) Check for blockers...(5) Use Slack template..."
→ Follow the 5-step guidance
→ Apply to current release version
```

**Available Prompts:**
- `system_prompt` - Core agent identity and capabilities (always active)
- `feature_freeze_prep` - Preparing Feature Freeze announcements
- `code_freeze_prep` - Preparing Code Freeze announcements
- `release_status_check` - Providing comprehensive release status
- `risk_identification` - Identifying and communicating release risks
- `team_coordination` - Coordinating information across teams

**When to Use:**
- Starting a new type of task you haven't done before
- Need guidance on approach for complex scenarios
- Want to ensure you're following best practices
- Checking system prompt for core capabilities

---

### Sheet 5: Jira Queries

**Use for:** Finding pre-built JQL query templates

**Note:** This sheet uses lowercase snake_case headers (like agent skill frontmatter): `name`, `description`, `jql_template`, `placeholders`, `example`, `notes`

**Query Pattern:**
1. Search `name` or `description` columns for relevant keywords
2. Copy `jql_template` content
3. Replace placeholders from `placeholders` column with actual values
4. Check `example` for reference
5. Execute query using appropriate tool from Sheet 3

**Example:**
```
User: "Show me CVEs for release 1.9.0"
→ Search Sheet 5 `name` column for "CVE"
→ Find "Jira list of CVEs"
→ Read `jql_template`: project IN (RHIDP,rhdhbugs) AND fixVersion = "{{RELEASE_VERSION}}" and issuetype in (weakness, Vulnerability, bug) and summary ~ "CVE*"
→ Read `placeholders`: {{RELEASE_VERSION}}
→ Replace {{RELEASE_VERSION}} with "1.9.0"
→ Execute: get_issues_summary("project IN (RHIDP,rhdhbugs) AND fixVersion = '1.9.0' and issuetype in (weakness, Vulnerability, bug) and summary ~ 'CVE*'")
```

**Common Queries Quick Reference:**
- Active releases → "jira list of active release"
- Open issues → "jira list of open issues"
- Epics → "Jira list of epics"
- CVEs → "Jira list of CVEs"
- Feature demos → "Jira list of Feature demos"
- Release notes → "Jira list of release notes"
- Feature freeze → "Jira list of feature freeze issues"
- Code freeze → "Jira list of code freeze issues"

---

### Sheet 6: Actions & Workflows

**Use for:** Understanding multi-step workflows and action requirements

**Note:** This sheet uses lowercase snake_case headers (like agent skill frontmatter): `name`, `description`, `input_required`, `data_sources`, `tools`, `output_format`, `instructions`

**Query Pattern:**
1. Search `name` column for the task user requested
2. Read `description` to confirm this is the right action
3. Check `input_required` - ask user if you don't have this information
4. Review `data_sources` and `tools` columns
5. Execute `instructions` steps
6. Format output according to `output_format` column

**Example:**
```
User: "Get teams and leads"
→ Find "Retrieve Teams and Leads" in Sheet 6 `name` column
→ Read `description`: "Compile a structured list of all Active RHDH teams"
→ Read `data_sources`: "RHDH Team Spreadsheet, Sheet: Team"
→ Read `tools`: get_document_content()
→ Read `instructions`: "Filter by Status=Active, return Category, Team Name, Team ID, Leads, Slack Handles"
→ Execute workflow
→ Format as table
```

**Workflow Execution Pattern:**
1. Read `description` (understand WHAT you're producing)
2. Gather inputs from `input_required` ({{RELEASE_VERSION}}, {{TEAM_ID}}, etc.)
3. Execute `tools` in sequence (follow `instructions`)
4. Format output (reference `output_format` → Sheet 3)
5. Include traceability (Jira links, spreadsheet links)

---

### Sheet 7: Slack Templates

**Use for:** Generating freeze announcements and status updates

**Note:** This sheet uses lowercase snake_case headers (like agent skill frontmatter): `name`, `milestone`, `when_to_send`, `data_requirements`, `template_content`

**Query Pattern:**
1. Identify which milestone user is asking about (Feature Freeze, Code Freeze)
2. Identify whether it's an "Update" (before) or "Announcement" (on the date)
3. Look up template in `name` column
4. Review `data_requirements` - gather all required data first
5. Copy `template_content` exactly (preserve Markdown syntax)
6. Replace placeholders with actual data
7. Return in code block for easy copy-paste

**Example:**
```
User: "Create Feature Freeze update for 1.9.0"
→ Find "Feature Freeze Update" in Sheet 7 `name` column
→ Read `data_requirements`:
  1. Feature Freeze date - use get_issue(RHDHPLAN-XXX)
  2. Active engineering teams - use get_document_content(spreadsheet)
  3. Outstanding Release Notes - use get_issues_summary()
  4. Team issue counts - use get_issues_by_team()
→ Gather all data first
→ Copy template from `template_content` column
→ Replace {{RELEASE_VERSION}}, {{FEATURE_FREEZE_DATE}}, {{TEAM_NAME}}, {{ISSUE_COUNT}}, {{JIRA_LINK}}, {{LEAD_SLACK}}
→ Return in code block with triple backticks
```

**Template Placeholder Replacement Rules:**
- `{{RELEASE_VERSION}}` → Actual release version (e.g., "1.9.0")
- `{{FEATURE_FREEZE_DATE}}` → Date from Jira issue
- `{{TEAM_NAME}}` → From team spreadsheet
- `{{ISSUE_COUNT}}` → From get_issues_by_team() or get_issues_stats()
- `{{JIRA_LINK}}` → Full Jira search URL
- `{{LEAD_SLACK}}` → Slack handle from team spreadsheet
- Preserve ALL emojis, formatting, and Markdown syntax exactly

**Critical:** Format output in code block (triple backticks) for easy Slack copy-paste.

---

## Workflow Examples

### Example 1: User Asks for Release Status

**User Request:** "What's the status of release 1.9.0?"

**Your Process:**

1. **Understand intent** → User wants overview of open issues

2. **Check Sheet 6 (Actions & Workflows)**
   - Find "Retrieve list of open issues for release"
   - Input Required: {{RELEASE_VERSION}} = "1.9.0"
   - Tools to Use: get_issues_summary()
   - Output Format: "Summary format"

3. **Check Sheet 5 (Jira Queries)**
   - Find "jira list of open issues"
   - JQL Template: `project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND fixVersion = "{{RELEASE_VERSION}}" and status != closed`
   - Replace placeholder: `fixVersion = "1.9.0"`

4. **Check Sheet 3 (Tools Reference)**
   - Tool: get_issues_summary()
   - Parameters: jql_query, max_results=50

5. **Execute:**
   ```python
   get_issues_summary("project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND fixVersion = '1.9.0' and status != closed")
   ```

6. **Check Sheet 3 (Tools Reference, Category="Output Format")**
   - Format: "Summary"
   - Required: Total count + Jira search link

7. **Format response:**
   ```
   **Release 1.9.0 Status**

   Total open issues: 42

   [View in Jira](https://issues.redhat.com/issues/?jql=project%20IN%20...)
   ```

### Example 2: User Requests Feature Freeze Announcement

**User Request:** "Create the Feature Freeze announcement for 1.9.0"

**Your Process:**

1. **Check Sheet 7 (Slack Templates)**
   - Find "Feature Freeze Announcement" (not "Update")
   - Review "Data Requirements":
     - Open EPICs count
     - CVE issues count
     - Outstanding Release Notes count

2. **Gather data using Sheet 5 queries:**

   a. **EPICs:**
   - Sheet 5 → "Jira list of epics"
   - Sheet 3 → Use get_issues_stats()
   - Execute query

   b. **CVEs:**
   - Sheet 5 → "Jira list of CVEs"
   - Sheet 3 → Use get_issues_stats()
   - Execute query

   c. **Release Notes:**
   - Sheet 6 → "Retrieve outstanding Release Notes"
   - Follow workflow instructions

3. **Copy template from Sheet 7:**
   - Get full "Template Content"
   - Preserve ALL formatting, emojis, Markdown

4. **Replace placeholders:**
   - {{RELEASE_VERSION}} → "1.9.0"
   - {{EPIC_ISSUE_COUNT}} → Actual count from step 2a
   - {{JIRA_LINK}} → Jira search URL for epics
   - {{CVE_ISSUE_COUNT}} → Actual count from step 2b
   - {{OUTSTANDING_RELEASE_NOTES_ISSUE_COUNT}} → Count from step 2c

5. **Return in code block:**
   ````markdown
   ```
   :rotating_light: *RHDH 1.9.0 Feature Freeze* :rotating_light:

   Its Feature Freeze! To see the latest status use the [RHDH Release Tracking dashboard]...
   ...
   ```
   ````

### Example 3: User Asks About Teams

**User Request:** "Who are the engineering team leads?"

**Your Process:**

1. **Check Sheet 6 (Actions & Workflows)**
   - Find "Retrieve Teams and Leads"
   - Objective: "Compile structured list of all Active RHDH teams"
   - Data Sources: "RHDH Team Spreadsheet, Sheet: Team"
   - Tools to Use: get_document_content()

2. **Execute tool:**
   ```python
   get_document_content("1vQXfvID72qwqvLb17eyGOvnZXrZG7NBzTGv6RP9wvyM")
   ```

3. **Process data:**
   - Filter: Status = "Active"
   - Filter: Category = "Engineering" (user specified engineering)
   - Extract: Team Name, Team ID, Leads, Slack Handles

4. **Format response as table:**
   ```markdown
   | Team Name | Team ID | Leads | Slack Handles |
   |-----------|---------|-------|---------------|
   | ...       | ...     | ...   | ...           |
   ```

---

## Best Practices for AI Agents

### 1. Always Gather Data Before Filling Templates

**❌ Bad:**
```
User: "Create Feature Freeze update"
You: [Immediately outputs template with {{PLACEHOLDER}} values]
```

**✅ Good:**
```
User: "Create Feature Freeze update"
You: [Checks Sheet 7 for data requirements]
     [Gathers all required data first]
     [Replaces ALL placeholders with actual values]
     [Returns complete, ready-to-use message]
```

### 2. Use the Right Tool for the Job

**❌ Bad:**
```
Task: Get per-team issue counts
You: [Uses get_issues_summary() and manually counts by team]
```

**✅ Good:**
```
Task: Get per-team issue counts
You: [Checks Sheet 3 Tools Reference]
     [Finds get_issues_by_team() in "Use When" column]
     [Uses dedicated tool for accurate counts]
```

### 3. Preserve Template Formatting Exactly

**❌ Bad:**
```
Template: :rotating_light: *RHDH 1.9.0 Feature Freeze* :rotating_light:
You output: RHDH 1.9.0 Feature Freeze
```

**✅ Good:**
```
You output: [Exact copy of template with emojis, Markdown, and formatting preserved]
```

### 4. Include Traceability Links

**❌ Bad:**
```
"There are 42 open issues"
```

**✅ Good:**
```
"There are [42](https://issues.redhat.com/issues/?jql=...) open issues"
```

### 5. Check Output Format Requirements

**❌ Bad:**
```
[Returns list of issues without Status, Priority, Assignee]
```

**✅ Good:**
```
[Checks Sheet 3 Tools Reference for required elements in Output Format category]
[Includes ALL required elements in output]
```

### 6. Replace ALL Placeholders

**❌ Bad:**
```
"Release {{RELEASE_VERSION}} has 42 issues"
```

**✅ Good:**
```
"Release 1.9.0 has 42 issues"
```

### 7. Validate Version Format

**❌ Bad:**
```
User: "Status for release 9"
You: [Assumes "9" is valid and queries]
```

**✅ Good:**
```
User: "Status for release 9"
You: [Checks Sheet 2 for version format: x.y.z]
     [Asks user: "Did you mean 1.9.0?"]
```

---

## Error Handling

### Missing Data in Workbook

**Scenario:** User asks for a query type not in Sheet 5

**Response:**
1. Check if you can construct the query from Sheet 2 (project keys) knowledge
2. Use general "jira list of open issues" template and add filters
3. Explain to user that you're using a custom query

### Placeholder Values Missing

**Scenario:** Template requires {{FEATURE_FREEZE_DATE}} but you can't retrieve it

**Response:**
1. Attempt to get from Jira issue (as Sheet 7 instructs)
2. If unavailable, ask user directly
3. Do NOT output template with {{PLACEHOLDER}} intact

### Tool Returns Empty Results

**Scenario:** get_issues_summary() returns 0 issues

**Response:**
1. Confirm this is accurate (not a query error)
2. Report to user: "0 issues found" with Jira link
3. Suggest user verify the query or release version

---

## Quick Reference Cheat Sheet

**Finding Prompts:** Sheet 4 (Prompts)
**Finding Queries:** Sheet 5 (Jira Queries)
**Finding Tools:** Sheet 3 (Tools Reference)
**Finding Workflows:** Sheet 6 (Actions & Workflows)
**Finding Templates:** Sheet 7 (Slack Templates)
**Finding Formats:** Sheet 3 (Tools Reference - Output Format category)
**Finding Config:** Sheet 2 (Configuration & Setup)
**Finding Best Practices:** Sheet 1 (Maintenance Guide)

**Tool Selection:**
- Counts only → `get_issues_stats()` or `get_issues_by_team()`
- Display issues → `get_issues_summary()` or `get_issues_detailed()`
- Per-team breakdown → `get_issues_by_team()` (NOT manual counting!)
- Single issue → `get_issue()`

**Common Workflows:**
- Release status → Sheet 6 → "Retrieve list of open issues for release"
- Teams → Sheet 6 → "Retrieve Teams and Leads"
- CVEs → Sheet 6 → "Retrieve list of CVEs"
- Blocker bugs → Sheet 6 → "Retrieve Blocker Bugs"

**Template Selection:**
- Before Feature Freeze → "Feature Freeze Update"
- On Feature Freeze → "Feature Freeze Announcement"
- Before Code Freeze → "Code Freeze Update"
- On Code Freeze → "Code Freeze Announcement"

---

## Summary

The Excel workbook is your **structured knowledge base**:

✅ **Use it to:**
- Look up JQL query templates
- Find the right tool for each task
- Follow multi-step workflows
- Fill Slack announcement templates
- Format output consistently

❌ **Don't use it for:**
- Simple conversational responses
- Strategic advice
- Information already in context

**Core workflow:**
1. User asks question
2. Check relevant sheet(s) for instructions
3. Gather required data using tools
4. Format output according to specifications
5. Return complete, actionable response

**Remember:** The workbook ensures consistency, accuracy, and completeness in Release Manager tasks. Always reference it for structured queries and templates.
