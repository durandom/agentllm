# Add Markdown Logging to Release Manager Scenario Tests

## Overview

Add rich markdown logging to `test_release_manager_scenarios.py` that captures the complete agent execution trace: reasoning, tool calls, responses, and validation results. Activated via `RELEASE_MANAGER_SCENARIO_LOGS=true` environment variable.

## Why This is Valuable

The test currently only uses `response.content` (final answer) but Agno's `RunOutput` object contains a wealth of debugging data:
- **Full conversation messages** (`response.messages`)
- **Tool calls with args and results** (`response.tools`)
- **Reasoning/thinking process** (`response.reasoning_content`, `response.reasoning_steps`)
- **Complete event trace** (`response.events`)
- **Metrics** (tokens, timing)

This logging will help debug agent behavior, understand decision patterns, and track performance.

## Output Structure

```
tmp/scenario_logs/
├── index.md                              # Auto-generated index with summary table
├── L1_01_workbook___list_queries.md
├── L1_02_workbook___get_template.md
├── L2_16_jql_template_application.md
└── comprehensive_20260201_143022/        # Timestamped for comprehensive test
    ├── comprehensive_summary.md
    ├── L1_01_workbook___list_queries.md
    └── ...
```

**Naming**: `L{level}_{id:02d}_{category_snake_case}.md` (matches pytest test IDs)

## Markdown Template Structure

Each log file contains:

1. **Header**: Status badge (✅/⚠️/❌), timestamp, duration
2. **Metadata**: Level, category, knowledge type, description
3. **Question**: The test query
4. **Execution Trace**:
   - **Reasoning**: Collapsed `<details>` (Gemini can be verbose)
   - **Tool Calls**: Expanded `<details>` with JSON args and results (truncated if > 1000 chars)
5. **Response**: Final answer and metadata (model, provider)
6. **Validation Results**: All validation messages with summary
7. **Metrics**: Token counts, timing
8. **Messages**: Collapsed section with full conversation history
9. **Events**: Collapsed section with execution event trace

**Design Choice**: Collapsible sections using HTML `<details>` tags for clean, scannable output.

## Critical Files to Modify

### 1. `tests/test_release_manager_scenarios.py`

**Add helper functions** (after line 350, before fixtures):
- `truncate_string(text, max_length)` - Truncate with "..." suffix
- `format_tool_call(tool, index)` - Format ToolExecution as markdown
- `generate_scenario_markdown(scenario, response, validation_messages, start_time, end_time, status)` - Build complete markdown
- `save_scenario_log(scenario, markdown_content)` - Save to file if env var set
- `generate_index_markdown(log_dir)` - Generate index.md with summary table
- `generate_comprehensive_summary(results, log_dir)` - Generate comprehensive test summary

**Modify `test_scenario()`** (lines 466-742):
```python
# Add timing
import time
start_time = time.time()

response = configured_agent.run(question, user_id=configured_user_id)

end_time = time.time()

# ... existing validation logic ...

# Determine status
status = "PASSED" if all("✅" in msg for msg in validation_messages) else \
         "PARTIAL" if any("✅" in msg for msg in validation_messages) else \
         "FAILED"

# Generate and save markdown log
markdown_content = generate_scenario_markdown(
    scenario=scenario,
    response=response,
    validation_messages=validation_messages,
    start_time=start_time,
    end_time=end_time,
    status=status,
)

log_path = save_scenario_log(scenario, markdown_content)
if log_path:
    print(f"\n📝 Scenario log saved to: {log_path}")
```

**Modify `test_comprehensive_scenarios()`** (lines 747-916):
```python
# Check if logging enabled
logging_enabled = os.getenv("RELEASE_MANAGER_SCENARIO_LOGS", "").lower() in ("true", "1", "yes")

if logging_enabled:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(f"tmp/scenario_logs/comprehensive_{timestamp}")
    log_dir.mkdir(parents=True, exist_ok=True)

# ... in loop, add timing and log generation ...

# After loop, generate comprehensive summary
if logging_enabled:
    summary_md = generate_comprehensive_summary(results, log_dir)
    summary_path = log_dir / "comprehensive_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"\n📊 Comprehensive summary saved to: {summary_path}")
```

### 2. `.gitignore`

Add:
```
tmp/scenario_logs/
```

### 3. `AGENTS.md` (optional but recommended)

Document the new capability in the "Testing" section.

## Implementation Details

### Helper Function: `format_tool_call()`

```python
def format_tool_call(tool: ToolExecution, index: int) -> str:
    """Format a single tool call as markdown."""
    status = "❌ Error" if tool.tool_call_error else "✅ Success"

    md = [f'<details open>\n<summary>🔧 Tool Call {index}: {tool.tool_name}</summary>\n\n']
    md.append(f'**Tool Call ID**: `{tool.tool_call_id}`  \n')
    md.append(f'**Status**: {status}\n\n')

    # Arguments
    md.append('#### Arguments\n\n')
    if tool.tool_args:
        args_json = json.dumps(tool.tool_args, indent=2, ensure_ascii=False)
        md.append(f'```json\n{truncate_string(args_json, 2000)}\n```\n\n')
    else:
        md.append('_No arguments_\n\n')

    # Result (truncate if > 1000 chars)
    md.append('#### Result\n\n')
    if tool.result:
        result_text = str(tool.result)
        if len(result_text) > 1000:
            md.append(f'```text\n{result_text[:1000]}\n... (truncated, full result: {len(result_text)} chars)\n```\n\n')
        else:
            md.append(f'```text\n{result_text}\n```\n\n')

    md.append('</details>')
    return ''.join(md)
```

### Helper Function: `generate_scenario_markdown()`

Build markdown in sections:
1. Header with status emoji, timestamp, duration
2. Metadata section
3. Question in code block
4. Execution trace (reasoning + tool calls)
5. Response section
6. Validation results
7. Metrics section
8. Messages (collapsed)
9. Events (collapsed)

**Key handling**:
- Use `truncate_string()` for long content
- Check for attribute existence with `hasattr()` and `getattr()`
- Use `<details>` for collapsible sections
- Format timestamps with `.isoformat()` or `.strftime()`

### Helper Function: `save_scenario_log()`

```python
def save_scenario_log(scenario: dict, markdown_content: str) -> Path | None:
    """Save scenario markdown log to file."""
    if not os.getenv("RELEASE_MANAGER_SCENARIO_LOGS", "").lower() in ("true", "1", "yes"):
        return None

    log_dir = Path("tmp/scenario_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename matching pytest ID format
    level = scenario["level"]
    scenario_id = scenario["id"]
    category = scenario["category"].lower().replace(" ", "_").replace("-", "_")
    filename = f"L{level}_{scenario_id:02d}_{category}.md"

    log_path = log_dir / filename
    log_path.write_text(markdown_content, encoding="utf-8")

    # Auto-generate index.md
    index_content = generate_index_markdown(log_dir)
    index_path = log_dir / "index.md"
    index_path.write_text(index_content, encoding="utf-8")

    return log_path
```

## Design Decisions

1. **Overwrite behavior**:
   - Individual tests: Overwrite each run (easier debugging)
   - Comprehensive test: Timestamped subdirectories (preserve history)

2. **Truncation thresholds**:
   - Tool args: 2000 chars
   - Tool results: 1000 chars
   - Message content: 1000 chars
   - (Can make configurable later if needed)

3. **Index generation**: Auto-generate on every scenario save (low overhead, always up-to-date)

4. **Mermaid diagrams**: Skip for MVP (adds complexity, may not render in all viewers)

## Verification

After implementation, test with:

```bash
# Single scenario
RELEASE_MANAGER_SCENARIO_LOGS=true pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[L1_01_workbook___list_queries] -v -s -m integration

# Check output
cat tmp/scenario_logs/L1_01_workbook___list_queries.md
cat tmp/scenario_logs/index.md

# Comprehensive test
RELEASE_MANAGER_SCENARIO_LOGS=true pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_comprehensive_scenarios -v -s -m integration

# Check timestamped output
ls tmp/scenario_logs/comprehensive_*/
```

**Verify**:
- ✅ Markdown renders correctly in VS Code/GitHub
- ✅ Tool calls formatted with JSON syntax highlighting
- ✅ Reasoning visible in collapsed section
- ✅ Validation results clear
- ✅ Metrics present
- ✅ Index.md links work
- ✅ Comprehensive summary accurate

## Edge Cases to Handle

- No tools called: Skip tool section gracefully
- No reasoning: Skip reasoning section
- Very long tool results: Truncate with "... (truncated)" message
- Unicode in response: Use UTF-8 encoding
- Failed scenarios: Show ❌ status badge
- Missing metrics: Use `hasattr()` checks, show "N/A" if missing
- Empty events list: Skip events section

## Estimated Effort

- Phase 1: Helper functions (1-2h)
- Phase 2: Markdown generation (2-3h)
- Phase 3: Test integration (1-2h)
- Phase 4: Index/summary generation (1-2h)
- Testing & refinement (1h)

**Total**: 6-10 hours
