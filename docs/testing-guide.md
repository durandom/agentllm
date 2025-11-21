# Store Manager Test Guide

## Parametrized Test Scenarios

The Store Manager agent tests now use pytest's parametrize feature, allowing you to run individual scenarios or groups of scenarios easily.

## Quick Reference

### Run a Single Scenario

```bash
# Run only scenario 1 (CSV Knowledge)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_01" -v -s -m integration

# Run only scenario 2 (Markdown Guides)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_02" -v -s -m integration
```

### Run Multiple Scenarios by Pattern

```bash
# Run all "quick validation" scenarios (1-3)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "quick_validation" -v -s -m integration

# Run all "knowledge base" scenarios (4-6)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "knowledge_base" -v -s -m integration

# Run all CSV-related scenarios
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "csv" -v -s -m integration

# Run all Jira integration scenarios (7-9)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "jira_integration" -v -s -m integration
```

### Run All Scenarios

```bash
# Run all 10 scenarios
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -v -s -m integration
```

### List Available Scenarios

```bash
# Show all available scenarios without running them
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -v -m integration --collect-only
```

## Available Test Scenarios

| ID | Category | Pattern Match Keywords |
|----|----------|------------------------|
| 1  | Quick Validation - CSV Knowledge | `scenario_01`, `quick_validation`, `csv_knowledge` |
| 2  | Quick Validation - Markdown Guides | `scenario_02`, `quick_validation`, `markdown_guides` |
| 3  | Quick Validation - Support Boundaries | `scenario_03`, `quick_validation`, `support_boundaries` |
| 4  | Knowledge Base - Specific Doc Citation | `scenario_04`, `knowledge_base`, `specific_doc_citation` |
| 5  | Knowledge Base - CSV Parsing | `scenario_05`, `knowledge_base`, `csv_parsing` |
| 6  | Knowledge Base - PDF + Markdown Integration | `scenario_06`, `knowledge_base`, `pdf`, `markdown_integration` |
| 7  | Jira Integration - Search | `scenario_07`, `jira_integration`, `search` |
| 8  | Jira Integration - JQL Query | `scenario_08`, `jira_integration`, `jql_query` |
| 9  | Jira Integration - Project Filtering | `scenario_09`, `jira_integration`, `project_filtering` |
| 10 | Complex Scenario - Multi-Use-Case | `scenario_10`, `complex_scenario`, `multi_use_case` |

## Notes

- **Jira scenarios (7-9)** require `STORE_MANAGER_JIRA_API_TOKEN` environment variable
- **All scenarios** require `GEMINI_API_KEY` environment variable
- Use `-s` flag to see detailed output during test execution
- Use `-v` flag for verbose test names
- Use `--collect-only` to preview which tests will run without executing them

## Examples

### Fast Development Workflow

```bash
# Test just CSV knowledge (fast validation)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_01" -v -s -m integration

# Test markdown docs (fast validation)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_02" -v -s -m integration
```

### Comprehensive Testing

```bash
# Run all non-Jira scenarios (if you don't have Jira configured)
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "not jira" -v -s -m integration

# Run everything
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -v -s -m integration
```

### Debugging Specific Features

```bash
# Test citation/source behavior
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "specific_doc_citation" -v -s -m integration

# Test complex multi-use-case handling
uv run pytest tests/test_store_manager_agent.py::TestStoreManagerIntegration::test_scenario -k "scenario_10" -v -s -m integration
```
