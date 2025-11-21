# RHDH Store Manager Agent

**Expert agent for Red Hat Developer Hub's plugin ecosystem management.**

## Quick Start

### 1. Set Environment Variables

Add to `.env.secrets`:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Required for Jira integration
STORE_MANAGER_JIRA_API_TOKEN=your_jira_api_token
```

### 2. Start the Proxy

```bash
nox -s proxy
```

### 3. Use the Agent

Select model: `agno/store-manager` in your chat interface.

---

## Capabilities

### 🔍 Use Case 1: Plugin Discovery & Availability
- Find available plugins for specific RHDH versions
- Check plugin compatibility and versions
- Query plugin status (GA/TP/Community)
- Access plugin version matrices from CSV files

**Example Questions:**
- "What plugins are available for RHDH 1.9?"
- "Which version of the Keycloak plugin should I use?"

### 🔧 Use Case 2: Plugin Migration & Building
- Convert Backstage static plugins to RHDH dynamic
- Guide on plugin development process
- Explain Dynamic Plugin Factory tool
- Advise on plugin code placement

**Example Questions:**
- "How do I convert my Backstage plugin to RHDH?"
- "Where should I place my plugin code?"

### 🏆 Use Case 3: Certification Program
- Explain partner plugin certification process
- Detail certification requirements
- Track certification applications (via Jira)
- Guide through 5-stage certification workflow

**Example Questions:**
- "How do I get my partner plugin certified?"
- "What are the certification requirements?"

### 📊 Use Case 4: Lifecycle & Maintenance
- Explain SemVer versioning strategy
- Guide deprecation processes
- Search for CVEs affecting plugins (via Jira)
- Clarify Plugin Maintainer responsibilities

**Example Questions:**
- "What's the SemVer strategy for plugins?"
- "How do I handle CVEs in my plugin?"

### 🎯 Use Case 5: Support Boundaries
- Distinguish GA vs TP vs Community support
- Explain support SLAs and escalation
- Clarify team responsibilities
- Guide on support channels

**Example Questions:**
- "What's the difference between GA and Tech Preview?"
- "Who do I contact for plugin issues?"

### 📅 Use Case 6: Release Planning
- Provide RHDH release schedules (from CSV files)
- Explain Y-stream vs Z-stream releases
- Search for release blockers (via Jira)
- Guide plugin-RHDH release coordination

**Example Questions:**
- "When is the next RHDH release?"
- "Are there any release blockers for RHDH 1.9?"

### 📋 Use Case 7: Metadata & Registry
- Explain plugin metadata requirements
- Guide plugin.yaml creation
- Describe registry publishing workflows
- Detail metadata standardization

**Example Questions:**
- "What metadata fields are required?"
- "How do I publish to registry.redhat.io?"

### 👥 Use Case 8: Team Coordination
- Clarify team roles and responsibilities
- Explain Plugin Maintainer vs Store Manager
- Describe COPE, Dynamic Plugin Team, Security Team
- Guide team coordination

**Example Questions:**
- "Who maintains the Keycloak plugin?"
- "What's the COPE team's role?"

---

## Knowledge Base

**Location:** `knowledge/store-manager/`

**Contents (24 files):**
- 9 Markdown files: Packaging guides, certification, strategy, team structure
- 1 PDF file: Plugin maintenance presentation
- 14 CSV files: Plugin catalogs, release schedules, version matrices

**Topics Covered:**
- RHDH Dynamic Plugin Packaging Guide
- Plugin Certification Program
- Release schedules and version matrices
- Team roles and responsibilities
- Plugin strategy and location guidance
- Engineering process documentation

---

## Jira Integration

**Read-Only Access to:**
- **RHIDP** - Red Hat Developer Hub project
- **RHDHPLAN** - RHDH Planning project

**Available Tools:**
- `get_issue(issue_key)` - Get details for specific issue
- `search_issues(jql_query)` - Search with JQL queries

**Example Jira Queries:**
- "Get details for RHIDP-1234"
- "Search RHIDP for plugin-related issues"
- "Find CVEs affecting plugins"
- "Show release blockers for RHDH 1.9"

**JQL Examples:**
```
project = RHIDP AND component = 'plugin-github' ORDER BY updated DESC
project IN (RHIDP, RHDHPLAN) AND text ~ 'certification'
project = RHDHPLAN AND labels = 'release-blocker'
```

---

## Architecture

### Components

**StoreManagerAgent** (BaseAgentWrapper)
- Execution interface
- Manages agent lifecycle
- Handles streaming/non-streaming

**StoreManagerAgentConfigurator** (AgentConfigurator)
- RAG knowledge base configuration
- Environment-based Jira toolkit initialization
- System instructions (8 use cases)
- No per-user configuration required

**StoreManagerAgentFactory** (AgentFactory)
- Plugin system registration
- Metadata provision
- Agent instance creation

### Key Features

1. **Environment-Based Configuration**
   - Jira token from `STORE_MANAGER_JIRA_API_TOKEN`
   - No per-user prompts or OAuth flows
   - Shared read-only access

2. **RAG Knowledge Integration**
   - Lazy loading with persistence
   - Hybrid search (vector + keyword)
   - Supports MD, PDF, CSV files
   - LanceDB vector storage

3. **Async Event Loop Handling**
   - Detects running event loops
   - Runs document loading in separate thread
   - Properly awaits all async operations
   - Ensures full indexing completion

---

## Testing

### Run Unit Tests

```bash
# All tests
pytest tests/test_store_manager_agent.py -v

# Specific test class
pytest tests/test_store_manager_agent.py::TestStoreManagerBasics -v

# Integration tests (requires API keys)
pytest tests/test_store_manager_agent.py -m integration -v
```

### Test Coverage

**13 unit tests:**
- ✅ Agent instantiation and parameters
- ✅ Factory metadata and creation
- ✅ Knowledge base configuration
- ✅ Jira toolkit integration (with/without token)
- ✅ System instructions validation
- ✅ Integration test (simple query)

### Manual Testing

See **[store-manager-test-questions.md](./store-manager-test-questions.md)** for:
- 58+ test questions across 8 use cases
- Complex multi-use-case scenarios
- Jira integration tests
- Knowledge base coverage tests
- Negative test cases

---

## Files

### Implementation
- `src/agentllm/agents/store_manager_agent.py` - Wrapper and factory
- `src/agentllm/agents/store_manager_agent_configurator.py` - Configurator
- `pyproject.toml` - Entry point registration
- `proxy_config.yaml` - Model configuration

### Testing
- `tests/test_store_manager_agent.py` - Unit tests
- `docs/agents/store-manager-test-questions.md` - Test questions

### Knowledge Base
- `knowledge/store-manager/` - Documentation (24 files)

---

## Troubleshooting

### Knowledge Base Not Loading

**Symptom:** "Knowledge loading failed: asyncio.run() cannot be called from a running event loop"

**Fix:** Ensure you have the latest code with async event loop handling. The fix uses ThreadPoolExecutor when running in async context.

**Check:**
```bash
grep -A 5 "_add_documents_async" src/agentllm/knowledge/manager.py
```

### Jira Tools Not Available

**Symptom:** Agent says Jira is not configured or doesn't use Jira tools

**Fix:** Set `STORE_MANAGER_JIRA_API_TOKEN` in `.env.secrets`

**Verify:**
```bash
echo $STORE_MANAGER_JIRA_API_TOKEN
```

### Missing aiofiles Dependency

**Symptom:** "aiofiles not installed"

**Fix:**
```bash
uv pip install aiofiles
# or
uv sync
```

---

## Development

### Adding Knowledge Files

1. Add files to `knowledge/store-manager/store-manager-docs/`
2. Supported formats: `.md`, `.pdf`, `.csv`
3. Delete LanceDB table to reindex:
   ```bash
   rm -rf tmp/lancedb/store_manager_knowledge.lance
   ```
4. Restart proxy - knowledge loads on first agent creation

### Modifying System Instructions

Edit `_build_agent_instructions()` in `store_manager_agent_configurator.py`

### Adding Jira Capabilities

Modify `_get_additional_toolkits()` in configurator to change Jira permissions:
```python
jira_toolkit = JiraTools(
    token=jira_token,
    server_url="https://issues.redhat.com",
    get_issue=True,        # Read issues
    search_issues=True,    # Search with JQL
    add_comment=False,     # Disable write access
    create_issue=False,    # Disable write access
)
```

---

## References

- **Main Documentation:** [store-manager.md](../../AGENTS.md#available-agents)
- **Test Questions:** [store-manager-test-questions.md](./store-manager-test-questions.md)
- **Agent Architecture:** [AGENTS.md](../../AGENTS.md)
- **Knowledge Management:** [../knowledge-management.md](../knowledge-management.md)
