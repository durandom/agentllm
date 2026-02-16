---
description: Run Release Manager integration tests with AI analysis
argument-hint: [test-spec] [--local-sheets]
model: haiku
---

# Release Manager Test Runner

Run Release Manager integration tests with intelligent analysis of results. This command spawns Haiku agents to execute tests and analyze failures/successes.

## Purpose

This command helps validate the Release Manager agent by:
- Running integration tests against real Jira/GDrive APIs
- Analyzing test results with AI to identify root causes
- Providing actionable feedback on test failures
- Validating progressive complexity (L1→L4) test architecture

## Arguments

- `test-spec` (optional) - Which tests to run
  - If omitted: List available tests and prompt for selection
  - `all` - Run all scenarios
  - `1-15` - Run specific scenario by number
  - `level-1`, `level-2`, `level-3`, `level-4` - Run all tests at a level
  - Examples: `5`, `level-1`, `all`

- `--local-sheets` (optional flag) - Use local CSV sheets instead of Google Drive
  - Default: Fetches workbook from Google Drive (requires OAuth)
  - With flag: Uses `exports/release manager_sheets/*.csv`

## Available Test Levels

**Level 1: Single-Toolkit** (basic queries, simple reasoning)
- Tests basic toolkit access and simple queries
- Each uses ONE toolkit and validates data retrieval

**Level 2: Cross-Toolkit** (combine data from multiple sources)
- Tests ability to combine data from multiple toolkits
- Requires understanding relationships between data sources

**Level 3: Structured Workflows** (multi-step processes with templates)
- Tests multi-step processes following workflow instructions
- Requires planning, data gathering, and template filling

**Level 4: Advanced Analysis** (complex reasoning, risk analysis, accuracy)
- Tests advanced capabilities: accuracy validation, risk analysis
- Proactive suggestions and multi-factor reasoning

## Workflow

### 1. Discover Available Tests

First, run `just rm-test` without arguments to list available scenarios:

```bash
just rm-test
```

Parse the output to identify:
- Scenario IDs (1-25 in the output, maps to test IDs)
- Level grouping (L1-L4 prefix)
- Test questions
- Available commands (all, level-1 through level-4, specific numbers)

### 2. Determine Test Spec

**If user provided test-spec argument ($1):**
- Validate it matches available options (all, 1-25, level-1 through level-4)
- If invalid, list available options and ask for clarification

**If no argument provided:**
- Present the list from `just rm-test`
- Ask user which tests to run using AskUserQuestion tool (max 4 options):
  - Option 1: "Level 1 only (Recommended)" - 15 tests, basic validation
  - Option 2: "All scenarios (full suite)" - 25 tests, comprehensive
  - Option 3: "Specific level (2, 3, or 4)" - Will ask which level
  - Option 4: "Single scenario" - Will ask for number

**If user selects "Specific level":**
- Ask for the level number (2, 3, or 4)

**If user selects "Single scenario":**
- Ask for the scenario number (1-25)

### 3. Check Workbook Source Preference

**If --local-sheets flag is NOT present in arguments:**
- Ask user using AskUserQuestion (max 3 options):
  - Option 1: "Google Drive (default)" - Requires OAuth
  - Option 2: "Local CSV sheets (--local-sheets)" - No OAuth needed
  - Option 3: "Auto-detect (use local if GDrive unavailable)"

### 4. Determine Scenario List

Based on test spec, build list of individual scenario IDs to run:

**Examples:**
- `all` → [1, 2, 3, ..., 25]
- `level-1` → [1, 2, 3, ..., 15]
- `level-2` → [16, 17, 18, 19]
- `5` → [5]

**CRITICAL**: Each scenario ID will be run in its own Haiku agent!

### 5. Spawn Agents in Batches (MAX 4 CONCURRENT)

**For each batch of up to 4 scenarios:**

1. **Spawn background Haiku agents** using Task tool with `run_in_background=True`:
   - `subagent_type`: "general-purpose"
   - `model`: "haiku"
   - `run_in_background`: true
   - `prompt`: Detailed prompt for analyzing single scenario (see below)

2. **Wait for batch to complete** before spawning next batch

3. **Collect results** from each agent's output file

**Agent Prompt Template:**

```
Run Release Manager integration test scenario <ID> and analyze the result.

CRITICAL INSTRUCTIONS:
1. Run ONLY scenario <ID> using: just rm-test <ID> [--local-sheets]
2. Capture the FULL output (exit code, test logs, validation results)
3. Analyze the result and provide structured output (see format below)

Test Details:
- Scenario ID: <ID>
- Level: <L1/L2/L3/L4>
- Category: <category>
- Question: <question>

Workbook Source: <Google Drive | --local-sheets>

Expected Output Format:
```json
{
  "scenario_id": <ID>,
  "status": "PASSED" | "FAILED" | "PARTIAL",
  "exit_code": <0 or non-zero>,
  "response_length": <chars>,
  "keywords_found": [<list>],
  "validation_results": [<list of validation messages>],
  "analysis": {
    "what_worked": [<list>],
    "what_failed": [<list>],
    "root_cause": "<string>",
    "recommendations": [<list>]
  },
  "response_preview": "<first 200 chars>"
}
```

Analysis Guidelines:
- If PASSED: Focus on what validation criteria were met
- If FAILED: Identify root cause (toolkit access, OAuth, agent reasoning, etc.)
- Check for patterns: Missing keywords, no response, errors, wrong tools used
- For count accuracy tests: Extract reported vs actual count, flag mismatches
- Progressive complexity: L1 failures are CRITICAL, L4 failures may be reasoning issues

Run the test now and provide the JSON analysis.
```

### 6. Analyze Individual Results

Each Haiku agent provides analysis in this format:

**PASSED Example:**
```json
{
  "scenario_id": 5,
  "status": "PASSED",
  "exit_code": 0,
  "response_length": 450,
  "keywords_found": ["release status", "workflow", "instructions"],
  "validation_results": [
    "✅ Response length: 450 chars",
    "✅ Found keywords: ['release status', 'workflow', 'instructions']",
    "✅ Includes workbook context"
  ],
  "analysis": {
    "what_worked": [
      "Agent correctly retrieved workflow instructions",
      "Response included all expected keywords",
      "Cited workbook as source"
    ],
    "what_failed": [],
    "root_cause": null,
    "recommendations": []
  },
  "response_preview": "To generate a release status update, follow these steps: 1. Execute 'jira list of active release' to get release versions..."
}
```

**FAILED Example:**
```json
{
  "scenario_id": 14,
  "status": "FAILED",
  "exit_code": 1,
  "response_length": 0,
  "keywords_found": [],
  "validation_results": [
    "❌ Missing expected keywords: ['schedule', 'future']",
    "⚠️  No response returned"
  ],
  "analysis": {
    "what_worked": [],
    "what_failed": [
      "Agent returned error: 'Spreadsheet not accessible'",
      "Missing keywords: ['schedule', 'future']"
    ],
    "root_cause": "Google Drive OAuth not configured - agent tried to access spreadsheet 1knVzlMW0l0X4c7gkoiuaGql1zuFgEGwHHBsj-ygUTnc but received 401 Unauthorized",
    "recommendations": [
      "Run 'just first-user' to check token status",
      "Run 'nox -s proxy' to configure Google OAuth",
      "OR: Use '--local-sheets' flag to bypass GDrive"
    ]
  },
  "response_preview": null
}
```

### 7. Aggregate Results & Provide Summary

**Background Agent Management:**

1. **Track agent IDs and output files** for each spawned agent
2. **Display progress** as agents complete (e.g., "3/15 tests complete...")
3. **Poll output files** periodically using Read tool to check completion
4. **Parse JSON results** from each agent's output
5. **Handle failures gracefully** (agent crashes, timeouts, malformed JSON)

**Batching Example (15 Level 1 tests):**
```
Batch 1: Spawn agents for scenarios 1, 2, 3, 4 → Wait for completion
Batch 2: Spawn agents for scenarios 5, 6, 7, 8 → Wait for completion
Batch 3: Spawn agents for scenarios 9, 10, 11, 12 → Wait for completion
Batch 4: Spawn agents for scenarios 13, 14, 15 → Wait for completion
```

**After collecting all JSON results**, aggregate and provide summary:

```markdown
## 📊 Release Manager Test Results

**Test Scope**: <test-spec description>
**Workbook Source**: <Google Drive | Local CSV sheets>
**Total Tests**: <N>
**Execution Time**: <duration>

**Results:**
- ✅ Passed: <N>
- ⚠️  Partial: <N> (some validations failed)
- ❌ Failed: <N>

**Success Rate**: <percentage>%

**Level Breakdown:**
| Level | Passed | Partial | Failed | Status |
|-------|--------|---------|--------|--------|
| L1    | N      | N       | N      | ✅/⚠️/❌ |
| L2    | N      | N       | N      | ✅/⚠️/❌ |
| L3    | N      | N       | N      | ✅/⚠️/❌ |
| L4    | N      | N       | N      | ✅/⚠️/❌ |

**Individual Test Results:**

<For each test, show one-line summary:>
✅ L1_01: Workbook - List Queries (450 chars, all validations passed)
✅ L1_02: Workbook - Get Template (380 chars, all validations passed)
⚠️  L1_03: Jira - Simple Count (290 chars, missing citation)
❌ L1_14: GDrive - Future Release Dates (OAuth not configured)
...

**Critical Issues:**
<List any critical failures, especially count accuracy bugs and L1 failures>

1. 🔴 L4_23 count accuracy failure - pagination bug (HIGH PRIORITY)
2. 🟡 L1_14, L1_15 GDrive tests failed - OAuth not configured
3. 🟡 L1_03, L1_04 missing citations (minor)

**Root Cause Analysis:**
<Group failures by root cause>

**Configuration Issues (2 failures):**
- L1_14, L1_15: Google Drive OAuth not configured
  - Fix: Run `nox -s proxy` OR use `--local-sheets`

**Agent Bugs (1 failure):**
- L4_23: Count accuracy - reported 15 but actual is 98
  - Fix: Investigate pagination in get_issues_stats()

**Minor Issues (2 partial passes):**
- L1_03, L1_04: Missing source citations
  - Agent used correct tools but didn't mention source

**Recommended Actions:**
1. **CRITICAL**: Fix pagination bug in L4_23 count accuracy test
2. **HIGH**: Configure Google Drive OAuth or commit to using --local-sheets
3. **MEDIUM**: Improve agent prompts to include source citations
4. **VERIFY**: Re-run L1 tests after fixes to ensure foundation is solid

**Next Steps:**
<Provide actionable roadmap based on results>

If L1 has failures: "Fix L1 issues first - higher levels depend on L1 foundation"
If only L4 fails: "L1-L3 solid, focus on advanced reasoning improvements"
If configuration issues: "Set up OAuth tokens to unlock full test suite"
```

## Analysis Guidelines

### Progressive Complexity Validation

**Level 1 failures are CRITICAL:**
- If L1 fails, L2-L4 are unreliable
- Focus on fixing L1 first (toolkit access, basic queries)
- L1 failures often indicate:
  - Missing OAuth tokens (Jira, GDrive)
  - Workbook not accessible
  - Basic toolkit methods broken

**Level 2-3 failures indicate:**
- Agent reasoning issues (can't combine data sources)
- Workflow comprehension problems
- Template/placeholder substitution bugs

**Level 4 failures indicate:**
- Advanced reasoning gaps
- Count accuracy bugs (pagination)
- Risk analysis logic issues

### Common Failure Patterns

**"No configured user found":**
- Run `just first-user` to check token status
- Suggest: `nox -s proxy` to configure OAuth

**"Workbook not found" or "Sheet not found":**
- Check `RELEASE_MANAGER_WORKBOOK_GDRIVE_URL` is set
- Suggest: Use `--local-sheets` flag

**Missing keywords but agent ran tools:**
- Check response quality (too short? wrong format?)
- Check if agent used correct tools (see tool call logs)
- May indicate prompt/instruction issue

**Count mismatch (accuracy tests):**
- CRITICAL BUG - pagination not working
- Compare agent's count vs actual Jira count
- Check if agent used `get_issues_stats()` vs manual counting

### Best Practices for Analysis

1. **Be specific**: Don't say "test failed" - explain WHAT failed and WHY
2. **Provide context**: Reference the test's purpose and validation criteria
3. **Actionable recommendations**: Suggest concrete fixes, not vague advice
4. **Progressive debugging**: If L1 fails, recommend fixing L1 before L2-L4
5. **Pattern recognition**: Identify if failures are systematic (e.g., all GDrive tests fail → OAuth issue)

## Usage Examples

### List available tests (interactive)
```bash
/rm-test
# Shows all 25 scenarios
# Asks which to run (Level 1, All, Specific level, Single scenario)
# Asks workbook source (Google Drive or --local-sheets)
# Spawns background Haiku agents (max 4 concurrent)
# Aggregates results and provides summary
```

### Run Level 1 only (recommended first run)
```bash
/rm-test level-1
# Runs 15 scenarios in 4 batches of 4, 4, 4, 3
# ~5-7 minutes total
# Best for validating foundation
```

### Run all tests
```bash
/rm-test all
# Runs all 25 scenarios in 7 batches
# ~12-15 minutes total
# Comprehensive validation
```

### Run specific scenario
```bash
/rm-test 5
# Runs only scenario 5
# ~1-2 minutes
# Good for debugging specific failures
```

### Run by level
```bash
/rm-test level-1
/rm-test level-2
/rm-test level-3
/rm-test level-4
```

## Example Execution Flow

**User runs:** `/rm-test level-1`

**Command executes:**

1. **Discover tests**: Runs `just rm-test` to get scenario list
2. **Ask preferences**:
   - Already specified: level-1
   - Asks: "Which workbook source?" → User selects "Google Drive"
3. **Build scenario list**: [1, 2, 3, ..., 15]
4. **Batch 1**: Spawn 4 background Haiku agents for scenarios 1-4
   ```
   🔄 Running tests (Batch 1/4)...
   - Scenario 1: Running...
   - Scenario 2: Running...
   - Scenario 3: Running...
   - Scenario 4: Running...
   ```
5. **Wait for Batch 1**: Poll output files every 10 seconds
   ```
   ✅ Scenario 1: PASSED (45 sec)
   ✅ Scenario 2: PASSED (38 sec)
   ⚠️  Scenario 3: PARTIAL (52 sec)
   ✅ Scenario 4: PASSED (41 sec)
   ```
6. **Batch 2-4**: Repeat for scenarios 5-8, 9-12, 13-15
7. **Aggregate results**: Parse all JSON outputs
8. **Display summary**:
   ```markdown
   ## 📊 Release Manager Test Results

   **Test Scope**: Level 1 (Single-Toolkit)
   **Workbook Source**: Google Drive
   **Total Tests**: 15
   **Execution Time**: 6m 23s

   **Results:**
   - ✅ Passed: 13
   - ⚠️  Partial: 2
   - ❌ Failed: 0

   **Success Rate**: 100% (87% perfect)

   **Individual Results:**
   ✅ L1_01: Workbook - List Queries (450 chars)
   ✅ L1_02: Workbook - Get Template (380 chars)
   ⚠️  L1_03: Jira - Simple Count (290 chars, missing citation)
   ...

   **Critical Issues:** None

   **Minor Issues:**
   - L1_03, L1_05: Missing source citations (agent didn't mention "Jira")

   **Recommended Actions:**
   1. ✅ L1 foundation is solid - all tests passed or partial
   2. OPTIONAL: Improve prompts to include explicit source citations
   3. READY: Proceed to Level 2 tests

   **Next Steps:**
   Run `/rm-test level-2` to validate cross-toolkit coordination
   ```

## Environment Requirements

**Required:**
- `GEMINI_API_KEY` - For agent model
- `AGENTLLM_TOKEN_ENCRYPTION_KEY` - For token decryption

**For Google Drive workbook (default):**
- `RELEASE_MANAGER_WORKBOOK_GDRIVE_URL` - Workbook URL
- `GDRIVE_CLIENT_ID` and `GDRIVE_CLIENT_SECRET` - OAuth credentials
- Configured user with GDrive tokens (via `nox -s proxy`)

**For Jira:**
- Configured user with Jira tokens (via `nox -s proxy`)

**To bypass Google Drive:**
- Use `--local-sheets` flag
- Requires `exports/release manager_sheets/*.csv` to exist

## Output Format

The command should:
1. **Show test execution in real-time** (stream pytest output)
2. **Provide AI analysis after completion** (parse results and analyze)
3. **Use clear visual formatting** (✅/⚠️/❌ emojis, tables, code blocks)
4. **Focus on actionable insights** (not just pass/fail counts)

## Implementation Details

### Spawning Background Agents

**Use the Task tool with these parameters:**

```python
Task(
    subagent_type="general-purpose",
    model="haiku",
    run_in_background=True,
    description=f"Test RM scenario {scenario_id}",
    prompt=f"""
Run Release Manager integration test scenario {scenario_id} and analyze the result.

CRITICAL INSTRUCTIONS:
1. Run ONLY scenario {scenario_id} using: just rm-test {scenario_id} {sheets_flag}
2. Capture the FULL output (exit code, test logs, validation results)
3. Extract key information and provide JSON analysis

Test Details:
- Scenario ID: {scenario_id}
- Level: {level}
- Category: {category}
- Question: {question}
- Expected Keywords: {keywords}

Workbook Source: {workbook_source}

Your Task:
1. Execute: just rm-test {scenario_id} {sheets_flag}
2. Analyze the pytest output
3. Extract validation results (✅/⚠️/❌ messages)
4. Determine status: PASSED (exit 0, all validations ✅), PARTIAL (exit 0, some ⚠️), FAILED (exit non-zero or missing keywords)
5. Identify root cause if failed
6. Provide actionable recommendations

Output this EXACT JSON format:
{{
  "scenario_id": {scenario_id},
  "status": "PASSED" | "FAILED" | "PARTIAL",
  "exit_code": <number>,
  "response_length": <number>,
  "keywords_found": [<list>],
  "validation_results": [<list of strings>],
  "analysis": {{
    "what_worked": [<list>],
    "what_failed": [<list>],
    "root_cause": "<string or null>",
    "recommendations": [<list>]
  }},
  "response_preview": "<string or null>"
}}

CRITICAL: Return ONLY valid JSON. No markdown, no explanations, just JSON.
"""
)
```

**The Task tool returns:**
- `task_id`: Use this to track the agent
- `output_file`: Path to read results (e.g., `/tmp/task_abc123.log`)

### Polling Agent Status

**While agents are running:**

```python
# Check agent status by reading output file
Read(file_path=output_file)

# Look for completion indicators:
# - JSON appears at end of output
# - Agent says "Task complete"
# - No new output for 30+ seconds
```

**Batch completion check:**
- Poll all 4 agents' output files
- When all show completion (or timeout after 5 minutes), proceed to next batch
- If agent crashes, record as FAILED with error details

### Parsing Agent Results

**Each agent's output file contains:**
1. Agent's reasoning and tool calls (streaming output)
2. Test execution output (from `just rm-test`)
3. Final JSON result (at the end)

**Extract JSON:**
```python
# Read last 2000 lines of output file
# Find JSON block (between { and })
# Parse and validate
# Handle malformed JSON gracefully (record as agent error)
```

### Error Handling

**If agent fails to produce JSON:**
- Record as "FAILED" with error: "Agent failed to analyze test"
- Include raw output for debugging
- Continue with remaining tests

**If test times out (>5 minutes):**
- Mark as "TIMEOUT"
- Kill background agent
- Suggest running manually to debug

**If JSON is malformed:**
- Attempt to extract status from pytest output
- Fallback to simple PASSED/FAILED based on exit code

## Important Notes

- **Use Haiku model**: This command uses Haiku for cost efficiency (many test analyses)
- **Max 4 concurrent agents**: Prevents overwhelming system resources
- **Each agent is isolated**: One test per agent for clean analysis
- **Background execution**: Don't block while tests run (~1-2 min each)
- **Graceful degradation**: If agent fails, fallback to basic pass/fail from exit code
- **Respect AGNO_DEBUG**: If `AGNO_DEBUG=true`, agents will see tool call logs
- **Progressive validation**: Each level builds on previous level validations
- **Count accuracy is critical**: Any count mismatch is a HIGH PRIORITY bug

## Related Commands

- `/catchup` - Review recent changes before running tests
- `just rm-test` - Direct test execution (no AI analysis)
- `just dev` - Start development stack with hot reload
- `just first-user` - Check configured user tokens

## Version

This command reflects the Release Manager test suite as of **2025-02-01** with 25 progressive complexity scenarios (L1-L4).
