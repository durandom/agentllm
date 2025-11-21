# Store Manager Comprehensive Test Guide

## Overview

The comprehensive test (`test_comprehensive_scenarios`) runs **10 key scenarios** as a single test to validate:
- ✅ Knowledge base coverage and RAG retrieval
- ✅ CSV, Markdown, and PDF file parsing
- ✅ Jira integration (when token configured)
- ✅ Multi-use-case handling
- ✅ Response quality and source citations

This test is designed for **iterative improvement** of the knowledge base and tooling.

---

## Running the Test

### With Output (Recommended)

```bash
# Run with full output to see responses
pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s

# Or use nox
nox -s test -- tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s
```

### Without Jira (Skips Jira Scenarios)

```bash
# Only test knowledge base scenarios (scenarios 1-6, 10)
# Jira scenarios (7-9) will be skipped
unset STORE_MANAGER_JIRA_API_TOKEN
pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s
```

### With Jira (All Scenarios)

```bash
# Set Jira token first
export STORE_MANAGER_JIRA_API_TOKEN=your_token_here

# Run all 10 scenarios
pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s
```

---

## Test Scenarios

### 🔍 Scenario 1: CSV Knowledge
**Question:** "What plugins are available for RHDH 1.9?"
- **Tests:** CSV file parsing from plugin catalogs
- **Expected:** Plugin list with version info
- **Should cite:** Yes (CSV file reference)

### 📝 Scenario 2: Markdown Guides
**Question:** "How do I convert my Backstage plugin to RHDH?"
- **Tests:** Markdown documentation retrieval
- **Expected:** Step-by-step migration guide
- **Should cite:** Yes (Packaging Guide reference)

### 🎯 Scenario 3: Support Boundaries
**Question:** "What's the difference between GA and Tech Preview?"
- **Tests:** Support level definitions
- **Expected:** Clear GA vs TP distinction
- **Should cite:** Yes (documentation reference)

### 📚 Scenario 4: Specific Doc Citation
**Question:** "What does the RHDH Dynamic Plugin Packaging Guide say about SemVer?"
- **Tests:** Targeted document search
- **Expected:** SemVer versioning rules (Major/Minor/Patch)
- **Should cite:** Yes (specific guide reference)

### 📅 Scenario 5: CSV Parsing
**Question:** "According to the release schedule, when is the next RHDH release?"
- **Tests:** CSV release schedule parsing
- **Expected:** Release dates and milestones
- **Should cite:** Yes (release schedule CSV)

### 🏆 Scenario 6: PDF + Markdown Integration
**Question:** "What are the certification requirements for partner plugins?"
- **Tests:** Multi-source information aggregation
- **Expected:** Certification process and requirements
- **Should cite:** Yes (certification docs)

### 🔧 Scenario 7: Jira Search (requires token)
**Question:** "Search RHIDP for plugin-related issues"
- **Tests:** Jira search tool usage
- **Expected:** RHIDP issue results
- **Should cite:** No (live data)

### 🐛 Scenario 8: Jira JQL Query (requires token)
**Question:** "Find CVEs affecting RHDH plugins"
- **Tests:** JQL query construction
- **Expected:** CVE-related issues
- **Should cite:** No (live data)

### 🚧 Scenario 9: Jira Filtering (requires token)
**Question:** "Show me release blockers for RHDH 1.9"
- **Tests:** Project and label filtering
- **Expected:** Release blocker issues
- **Should cite:** No (live data)

### 🎭 Scenario 10: Multi-Use-Case Complex
**Question:** "I want to create a new plugin, get it certified, and included in RHDH. Walk me through the complete process."
- **Tests:** Multi-use-case integration
- **Expected:** Complete end-to-end process
- **Should cite:** Yes (multiple sources)

---

## Understanding the Output

### During Test Execution

For each scenario, you'll see:

```
[1/10] 🧪 TESTING: Quick Validation - CSV Knowledge
Question: What plugins are available for RHDH 1.9?
--------------------------------------------------------------------------------
✅ Response length: 1234 chars
✅ Found keywords: ['plugin', '1.9', 'available']
✅ Includes source citation

📄 Response Preview:
According to the RHDH Packaged Plugins catalog, here are the plugins available...

✅ Status: PASSED
```

### Validation Criteria

Each scenario is validated for:
1. **Response Length** - Must be at least 50 characters
2. **Expected Keywords** - Must contain relevant keywords
3. **Source Citation** - Knowledge-based queries should cite sources

### Status Types

- **✅ PASSED** - All validations passed
- **⚠️  PARTIAL** - Response received but some validations failed
- **❌ FAILED** - Exception or error occurred
- **⏭️  SKIPPED** - Jira test skipped (no token)

### Final Summary

```
================================================================================
TEST SUMMARY
================================================================================
Total Scenarios: 10
  ✅ Passed: 7/7
  ⚠️  Partial: 0/7
  ❌ Failed: 0/7
  ⏭️  Skipped: 3/10

📊 Detailed results saved to: tmp/store_manager_test_results.json
================================================================================
```

---

## Results File

Detailed results are saved to `tmp/store_manager_test_results.json`:

```json
{
  "timestamp": "2025-11-20T17:30:00.000000",
  "jira_enabled": false,
  "summary": {
    "total": 10,
    "passed": 7,
    "partial": 0,
    "failed": 0,
    "skipped": 3
  },
  "results": [
    {
      "id": 1,
      "category": "Quick Validation - CSV Knowledge",
      "question": "What plugins are available for RHDH 1.9?",
      "status": "PASSED",
      "response_length": 1234,
      "found_keywords": ["plugin", "1.9", "available"],
      "validation": [...]
    },
    ...
  ]
}
```

Use this file to:
- Track improvements over time
- Compare results after knowledge base updates
- Identify patterns in failing scenarios
- Export for reporting

---

## Iterating on the Test

### When to Run

Run this test after:
- ✅ Adding new knowledge base files
- ✅ Updating system instructions
- ✅ Modifying Jira integration
- ✅ Changing RAG configuration
- ✅ Updating dependencies (Agno version, etc.)

### Improving Results

#### If Scenario Fails

1. **Check the response preview** - Does it answer the question?
2. **Review validation messages** - Which criteria failed?
3. **Examine the knowledge base** - Is the information available?
4. **Check system instructions** - Does the agent know to use that source?

#### If No Source Citation

Add citation patterns to system instructions:
```python
"When referencing knowledge base documents, always cite the source:"
"- For CSVs: 'According to the RHDH Packaged Plugins catalog...'"
"- For guides: 'The RHDH Dynamic Plugin Packaging Guide states...'"
```

#### If Keywords Missing

- Review expected keywords - Are they too specific?
- Check knowledge base content - Does it use those terms?
- Update system instructions to emphasize key terminology

#### If Response Too Short

- Agent may need more explicit instructions to provide detail
- Knowledge base may be missing information
- RAG retrieval may not be finding relevant content

### Adding New Scenarios

Edit `test_comprehensive_scenarios` in `tests/test_store_manager_agent.py`:

```python
{
    "id": 11,
    "category": "Your Category",
    "question": "Your test question?",
    "expected_keywords": ["keyword1", "keyword2"],
    "should_cite_source": True,
    "knowledge_type": "markdown",  # or "csv", "jira", "multi"
},
```

---

## Success Criteria

The test **passes** if:
- ✅ At least one scenario runs (not all skipped)
- ✅ No scenarios fail completely (errors/exceptions)
- ✅ At least 80% of run scenarios pass or are partial

The test **fails** if:
- ❌ All scenarios are skipped
- ❌ Any scenario fails with an exception
- ❌ Success rate below 80%

---

## Troubleshooting

### "No tests were run"

**Cause:** All scenarios were skipped (likely GEMINI_API_KEY not set)

**Fix:**
```bash
export GEMINI_API_KEY=your_key_here
```

### "X scenarios failed completely"

**Cause:** Exceptions during agent execution

**Fix:**
1. Check error messages in output
2. Verify knowledge base is indexed
3. Ensure proxy is running (if testing via proxy)
4. Check agent logs for details

### "Success rate too low: X%"

**Cause:** Too many scenarios have missing keywords or failed validations

**Fix:**
1. Review detailed results in `tmp/store_manager_test_results.json`
2. Identify common failure patterns
3. Update knowledge base or system instructions
4. Consider if expected keywords are too strict

### All Jira Tests Skipped

**Expected:** If `STORE_MANAGER_JIRA_API_TOKEN` not set

**To enable:**
```bash
export STORE_MANAGER_JIRA_API_TOKEN=your_jira_token
```

---

## Best Practices

### Regular Testing

```bash
# Quick validation (knowledge base only)
make test-store-manager

# Full validation (with Jira)
export STORE_MANAGER_JIRA_API_TOKEN=...
make test-store-manager-full
```

### Before Commits

Run the test before committing changes to:
- Knowledge base files
- System instructions
- Agent configurator
- Jira toolkit integration

### Benchmarking

Save results periodically:
```bash
# Run and save results with timestamp
pytest ... -v -s > test_results_$(date +%Y%m%d_%H%M%S).log
cp tmp/store_manager_test_results.json results_$(date +%Y%m%d_%H%M%S).json
```

Compare results over time to track improvements.

---

## Example Workflow

### 1. Baseline Test

```bash
# Run initial test
pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s

# Note: 2 scenarios failed (missing keywords)
```

### 2. Review Results

```bash
# Check detailed results
cat tmp/store_manager_test_results.json | jq '.results[] | select(.status != "PASSED")'
```

### 3. Improve Knowledge Base

```bash
# Add missing documentation
echo "Additional content about certification..." >> knowledge/store-manager/store-manager-docs/certification.md

# Reindex (delete LanceDB table)
rm -rf tmp/lancedb/store_manager_knowledge.lance
```

### 4. Update Instructions

Edit `src/agentllm/agents/store_manager_agent_configurator.py`:
```python
# Add more specific guidance about certification
"When asked about certification, reference the 5-stage process..."
```

### 5. Re-test

```bash
# Run again
pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s

# Note: Now all knowledge-based scenarios pass!
```

### 6. Compare

```bash
# Compare before/after
diff results_before.json tmp/store_manager_test_results.json
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Store Manager Comprehensive Test
  run: |
    pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_comprehensive_scenarios -v -s
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    # Optional: STORE_MANAGER_JIRA_API_TOKEN: ${{ secrets.JIRA_TOKEN }}

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: store-manager-test-results
    path: tmp/store_manager_test_results.json
```

---

## Related Documentation

- **[store-manager.md](./store-manager.md)** - Agent overview and capabilities
- **[store-manager-test-questions.md](./store-manager-test-questions.md)** - All 58+ test questions
- **[../knowledge-management.md](../knowledge-management.md)** - RAG knowledge system
