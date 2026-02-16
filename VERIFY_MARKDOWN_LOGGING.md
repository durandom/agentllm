# Verify Markdown Logging Implementation

This guide helps you verify the new markdown logging feature for Release Manager scenario tests.

## Quick Test

Run a single scenario with logging enabled:

```bash
# Single scenario test
RELEASE_MANAGER_SCENARIO_LOGS=true pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[L1_01_workbook___list_queries] -v -s -m integration
```

**Expected output**:
- Test runs normally
- At the end: `📝 Scenario log saved to: tmp/scenario_logs/L1_01_workbook___list_queries.md`
- Files created:
  - `tmp/scenario_logs/L1_01_workbook___list_queries.md` (scenario log)
  - `tmp/scenario_logs/index.md` (auto-generated index)

## Verify Log Content

```bash
# View the scenario log
cat tmp/scenario_logs/L1_01_workbook___list_queries.md

# View the index
cat tmp/scenario_logs/index.md
```

**Verify the scenario log contains**:
- ✅ Status badge (✅/⚠️/❌) in header
- ✅ Metadata section (level, category, knowledge type)
- ✅ Question in code block
- ✅ Execution Trace with:
  - Reasoning (collapsed `<details>`)
  - Tool Calls (expanded `<details>` with JSON args and results)
- ✅ Response section
- ✅ Validation Results with summary
- ✅ Metrics (duration, tokens)
- ✅ Messages (collapsed)
- ✅ Events (collapsed)

**Verify the index contains**:
- ✅ Summary table with Level, ID, Category, Status, Duration columns
- ✅ Clickable links to scenario logs
- ✅ Timestamp

## Test Comprehensive Run

Run all scenarios with timestamped logging:

```bash
RELEASE_MANAGER_SCENARIO_LOGS=true pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_comprehensive_scenarios -v -s -m integration
```

**Expected output**:
- `📁 Logging enabled: tmp/scenario_logs/comprehensive_YYYYMMDD_HHMMSS`
- All scenarios run and log individually
- At the end: `📊 Comprehensive summary saved to: tmp/scenario_logs/comprehensive_YYYYMMDD_HHMMSS/comprehensive_summary.md`

**Verify structure**:

```bash
ls -la tmp/scenario_logs/comprehensive_*/
```

Should contain:
- `comprehensive_summary.md` (overall summary)
- `L1_01_workbook___list_queries.md`
- `L1_02_workbook___get_template.md`
- ... (all other scenarios)

## Test Markdown Rendering

Open in VS Code or GitHub to verify:
- ✅ Collapsible sections work (`<details>` tags)
- ✅ Code blocks have syntax highlighting
- ✅ Tables render correctly
- ✅ Links work in index.md

## Verify Environment Variable Control

```bash
# Without env var - no logging
pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[L1_01_workbook___list_queries] -v -s -m integration

# Verify no log file created
ls tmp/scenario_logs/L1_01_workbook___list_queries.md 2>&1
# Should show: No such file or directory (if this was the first test)
```

## Edge Cases to Test

### 1. No tools called
Test a scenario that doesn't use tools (if any):
- Should show "_No tools called_" instead of crashing

### 2. Failed scenario
Force a failure by using an invalid question:
```bash
# Modify a scenario temporarily to use invalid input
# Verify the log shows ❌ FAILED status
```

### 3. Very long responses
- Tool results > 1000 chars should be truncated
- Tool args > 2000 chars should be truncated
- Should show "... (truncated, full length: N chars)"

## Integration with just Commands

Add to `just/release_manager.just` for convenience:

```bash
# Run scenario with logging
@test-scenario SCENARIO_ID:
    RELEASE_MANAGER_SCENARIO_LOGS=true pytest "tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario[{{SCENARIO_ID}}]" -v -s -m integration

# Run comprehensive test with logging
@test-comprehensive-logged:
    RELEASE_MANAGER_SCENARIO_LOGS=true pytest tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_comprehensive_scenarios -v -s -m integration
```

Then use:

```bash
just test-scenario L1_01_workbook___list_queries
just test-comprehensive-logged
```

## Troubleshooting

### Logs not being created

1. Check environment variable:
   ```bash
   echo $RELEASE_MANAGER_SCENARIO_LOGS
   # Should output: true
   ```

2. Check directory permissions:
   ```bash
   ls -ld tmp/
   # Should be writable
   ```

### Markdown not rendering correctly

1. Try different viewers:
   - VS Code with Markdown Preview
   - GitHub (if pushed to repo)
   - `mdcat` or `glow` CLI tools

2. Check for syntax errors:
   ```bash
   # Install markdownlint if needed
   npm install -g markdownlint-cli

   # Lint the generated files
   markdownlint tmp/scenario_logs/*.md
   ```

### Missing data in logs

The logging system uses `hasattr()` and `getattr()` for safe attribute access, so missing fields should show as "_N/A_" or "_No X available_" rather than crashing.

Check the test output for errors during log generation.

## Success Criteria

✅ Single scenario creates log file
✅ Log file contains all expected sections
✅ Index.md auto-generates with summary table
✅ Comprehensive test creates timestamped directory
✅ Comprehensive summary contains level breakdown
✅ Markdown renders correctly in VS Code/GitHub
✅ Collapsible sections work (`<details>` tags)
✅ Tool calls show JSON syntax highlighting
✅ Long content is properly truncated
✅ Without env var, no logs are created
✅ Failed scenarios still generate logs with error info

## Next Steps

After verification, consider:

1. **Update AGENTS.md** to document the feature
2. **Add to CI/CD** to generate logs on scheduled test runs
3. **Create dashboards** from the JSON/markdown data
4. **Track trends** across comprehensive test timestamps
