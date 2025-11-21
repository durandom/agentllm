# RHDH Store Manager Agent - Test Questions

Comprehensive test questions organized by use case to validate the Store Manager agent's capabilities.

## Setup Requirements

Before testing, ensure:
- ✅ `GEMINI_API_KEY` is set in `.env.secrets`
- ✅ `STORE_MANAGER_JIRA_API_TOKEN` is set (for Jira queries)
- ✅ Knowledge base exists at `knowledge/store-manager/` (24 files: 9 MD, 1 PDF, 14 CSV)
- ✅ Proxy is running: `nox -s proxy`

---

## Use Case 1: Plugin Discovery & Availability 🔍

**Purpose**: Test the agent's ability to answer questions about plugin availability, versions, and compatibility.

### Test Questions:

**Basic Discovery:**
- "What plugins are available for RHDH 1.9?"
- "Which plugins are included by default in RHDH?"
- "List all Tech Preview plugins"
- "What community plugins are available?"

**Version & Compatibility:**
- "Which version of the Keycloak plugin should I use?"
- "Is the OCM plugin compatible with RHDH 1.8?"
- "What's the latest version of the GitHub plugin?"
- "Show me the version matrix for plugins"

**Status Queries (uses Jira):**
- "What's the current status of the Ansible plugin?"
- "Search RHIDP for plugin-related issues"
- "Are there any GA plugins in development?"

**Expected Behavior:**
- Should query CSV files for plugin catalogs
- Should reference release schedules
- Should use Jira for real-time status when token is configured
- Should distinguish between GA, TP, and Community support levels

---

## Use Case 2: Plugin Migration & Building Support 🔧

**Purpose**: Test guidance on converting Backstage plugins to RHDH dynamic plugins.

### Test Questions:

**Migration Process:**
- "How do I convert my Backstage static plugin to RHDH dynamic?"
- "What's the process for building a custom plugin?"
- "Walk me through the Dynamic Plugin Factory tool"
- "What are the steps to migrate a Backstage plugin?"

**Plugin Placement:**
- "Where should I place my plugin code?"
- "Should my plugin go in rhdh-plugins or backstage/community-plugins?"
- "What's the difference between plugin locations?"

**Known Issues (uses Jira):**
- "Are there any known migration issues?"
- "Search for plugin migration problems in Jira"
- "What are common plugin conversion errors?"

**Expected Behavior:**
- Should reference RHDH Dynamic Plugin Packaging Guide
- Should cite Backstage Plugin Location Guidance
- Should provide step-by-step migration instructions
- Should mention the Dynamic Plugin Factory tool

---

## Use Case 3: Certification Program Guidance 🏆

**Purpose**: Test knowledge of the partner plugin certification program.

### Test Questions:

**Certification Process:**
- "How do I get my partner plugin certified?"
- "What are the certification requirements?"
- "Explain the 5-stage certification process"
- "What's the certification timeline?"

**Requirements:**
- "What documentation do I need for certification?"
- "What testing is required for plugin certification?"
- "Do I need to be a Red Hat Technology Partner?"

**Status Tracking (uses Jira):**
- "What's the status of certification applications?"
- "Search RHDHPLAN for certification-related issues"
- "Are there any plugins in certification review?"

**Expected Behavior:**
- Should reference RHDH Plugin Certification Program documentation
- Should explain all 5 stages clearly
- Should mention automated testing requirements
- Should cite listing locations (Extensions catalog, Solution Catalog)

---

## Use Case 4: Plugin Lifecycle & Maintenance 📊

**Purpose**: Test understanding of plugin maintenance, versioning, and security.

### Test Questions:

**Version Management:**
- "What's the SemVer strategy for plugins?"
- "When should I bump major vs minor vs patch version?"
- "How do Y-stream and Z-stream releases work?"
- "What's the Backstage version compatibility policy?"

**Deprecation:**
- "What's the plugin deprecation process?"
- "How do I deprecate a plugin?"
- "Are there any deprecated plugins I should know about?"

**Security (uses Jira):**
- "How do I handle CVEs in my plugin?"
- "Search for security issues affecting plugins"
- "What's the SLA for CVE remediation?"
- "Are there any active CVEs for RHDH plugins?"

**Team Responsibilities:**
- "What's a Plugin Maintainer responsible for?"
- "How do Plugin Maintainers coordinate with Store Manager?"
- "Who handles security patches?"

**Expected Behavior:**
- Should reference SemVer guidelines from packaging guide
- Should explain Major/Minor/Patch rules clearly
- Should search Jira for CVEs when asked
- Should clarify Plugin Maintainer vs Store Manager roles

---

## Use Case 5: Support Boundary Clarification 🎯

**Purpose**: Test ability to clarify support levels and responsibilities.

### Test Questions:

**Support Levels:**
- "What's the difference between GA, TP, and Dev Preview?"
- "Is the backstage-community XYZ plugin supported by Red Hat?"
- "What does Tech Preview support include?"
- "Which plugins have full Red Hat support?"

**Support Boundaries:**
- "Who do I contact for plugin issues?"
- "What's covered under RHDH support SLA?"
- "Can Red Hat help with community plugins?"
- "What's the escalation path for plugin bugs?"

**Team Structure:**
- "Who's responsible for plugin security?"
- "What does the COPE team do?"
- "What's the Dynamic Plugin Team's role?"

**Expected Behavior:**
- Should reference RHDH Roles and Responsibilities documentation
- Should clearly explain GA/TP/Community distinctions
- Should provide escalation paths
- Should clarify team boundaries (COPE, Dynamic Plugin Team, Security, etc.)

---

## Use Case 6: Release Planning & Coordination 📅

**Purpose**: Test knowledge of release schedules and coordination processes.

### Test Questions:

**Release Information:**
- "When is the next RHDH release?"
- "Which plugins are in RHDH 1.9?"
- "What's the release schedule for RHDH?"
- "When is feature freeze for the current release?"

**Coordination:**
- "How do I coordinate my plugin release with RHDH releases?"
- "What's the difference between Y-stream and Z-stream releases?"
- "How do I get my plugin into the next RHDH release?"

**Release Blockers (uses Jira):**
- "Are there any release blockers for RHDH 1.9?"
- "Search RHDHPLAN for release-related issues"
- "What plugins are blocking the current release?"

**Expected Behavior:**
- Should query release schedule CSV files
- Should search Jira for release blockers
- Should explain Y-stream vs Z-stream processes
- Should reference feature freeze handling

---

## Use Case 7: Metadata & Registry Management 📋

**Purpose**: Test guidance on plugin metadata and registry publishing.

### Test Questions:

**Metadata Requirements:**
- "What metadata fields are required for catalog listing?"
- "How do I create a plugin.yaml file?"
- "What should I put in the plugin metadata?"
- "Where does plugin metadata live?"

**Registry Publishing:**
- "How do I publish to registry.redhat.io?"
- "What's the difference between registry.redhat.io and quay.io?"
- "How do I publish my plugin to the catalog?"
- "What registries are used for RHDH plugins?"

**Standardization:**
- "What are the standardized metadata fields?"
- "What values can the 'support' field have?"
- "What's the required plugin.yaml format?"

**Expected Behavior:**
- Should reference metadata standardization documentation
- Should explain required fields (author, support, lifecycle)
- Should describe registry publishing workflows
- Should mention plugin.yaml requirements

---

## Use Case 8: Team Coordination & Responsibilities 👥

**Purpose**: Test understanding of team structure and ownership.

### Test Questions:

**Ownership:**
- "Who maintains the Keycloak plugin?"
- "How do I find the maintainer for a plugin?"
- "What's the Plugin Maintainer's responsibility?"

**Team Boundaries:**
- "What's the difference between Plugin Maintainer and Store Manager roles?"
- "What does the COPE team do vs Dynamic Plugin Team?"
- "Who's responsible for security patches?"
- "How does the Security Team work with Plugin Maintainers?"

**Coordination (uses Jira):**
- "Find the component owner for a plugin in Jira"
- "Search for plugin-related team coordination issues"

**Expected Behavior:**
- Should reference RHDH Roles and Responsibilities
- Should explain team boundaries clearly
- Should distinguish Plugin Maintainer, COPE, Dynamic Plugin Team, Security Team
- Should clarify coordination points between teams

---

## Complex Multi-Use-Case Questions

These questions test the agent's ability to integrate knowledge across multiple use cases:

**1. End-to-End Plugin Journey:**
> "I want to create a new plugin, get it certified, and included in RHDH. Walk me through the complete process."

Should cover: Building (Use Case 2) → Certification (Use Case 3) → Release Planning (Use Case 6) → Metadata (Use Case 7)

**2. Support Escalation:**
> "I found a security issue in a Tech Preview plugin. Who should I contact and what's the process?"

Should cover: Support Boundaries (Use Case 5) → Lifecycle/Security (Use Case 4) → Team Coordination (Use Case 8)

**3. Version Upgrade:**
> "How do I upgrade my plugin to the latest Backstage version and get it into the next RHDH release?"

Should cover: Lifecycle/Versioning (Use Case 4) → Release Planning (Use Case 6) → Team Coordination (Use Case 8)

**4. Community Plugin Adoption:**
> "Can a community plugin become officially supported? What's the process?"

Should cover: Support Boundaries (Use Case 5) → Certification (Use Case 3) → Lifecycle (Use Case 4)

---

## Jira Integration Test Questions

These specifically test Jira toolkit integration (requires `STORE_MANAGER_JIRA_API_TOKEN`):

### Direct Jira Queries:
- "Get details for RHIDP-1234" (replace with actual issue)
- "Search RHIDP for issues with label 'plugin-keycloak'"
- "Find all unresolved CVEs in RHIDP project"
- "Show me release blockers for RHDH 1.9"
- "Search RHDHPLAN for certification applications"

### JQL Query Tests:
- "Search for: project = RHIDP AND component = 'plugin-github' ORDER BY updated DESC"
- "Find issues: project IN (RHIDP, RHDHPLAN) AND text ~ 'migration'"
- "Query: project = RHDHPLAN AND labels = 'certification' AND status != 'Closed'"

**Expected Behavior:**
- Should use `get_issue()` tool for specific issue queries
- Should use `search_issues()` with JQL for searches
- Should provide working Jira links in responses
- Should combine Jira data with knowledge base information

---

## Knowledge Base Coverage Tests

Test that the agent can access different types of knowledge files:

### Markdown Files:
- "What does the RHDH Dynamic Plugin Packaging Guide say about SemVer?"
- "According to the Plugins Strategy doc, where should plugins be located?"
- "What does the Certification Program documentation say about Stage 3?"

### CSV Files:
- "Query the RHDH Packaged Plugins CSV for all GA plugins"
- "What does the release schedule CSV say about Q4 2025?"
- "List plugins from the packaged plugins spreadsheet"

### PDF File:
- "What does the Plugin Maintenance presentation say about responsibilities?"

**Expected Behavior:**
- Should cite specific documents when answering
- Should access CSV data for structured queries
- Should parse PDF content when relevant
- Should combine information from multiple sources

---

## Negative Test Cases

Test error handling and graceful degradation:

**1. No Jira Token:**
- Remove `STORE_MANAGER_JIRA_API_TOKEN` and ask: "Search Jira for plugins"
- Should gracefully explain Jira is not configured but still answer from knowledge base

**2. Invalid Jira Queries:**
- "Get details for INVALID-123" (non-existent issue)
- Should handle errors gracefully

**3. Ambiguous Questions:**
- "Tell me about plugins"
- Should ask for clarification or provide overview

**4. Out of Scope:**
- "How do I cook pasta?"
- Should politely redirect to RHDH plugin topics

---

## Success Criteria

For each test question, the agent should:
- ✅ Provide accurate information from knowledge base
- ✅ Cite specific source documents when applicable
- ✅ Use Jira tools appropriately when configured
- ✅ Combine multiple sources (docs + Jira + CSV) when relevant
- ✅ Provide actionable next steps
- ✅ Clarify support boundaries and team responsibilities
- ✅ Use appropriate technical terminology
- ✅ Link to Jira issues when referencing them

---

## Running Tests

### Unit Tests:
```bash
# Run all tests
nox -s test tests/test_store_manager_agent.py

# Run specific test class
pytest tests/test_store_manager_agent.py::TestStoreManagerBasics -v

# Run integration tests (requires API keys)
pytest tests/test_store_manager_agent.py -m integration -v
```

### Manual Testing:
1. Start proxy: `nox -s proxy`
2. Open chat interface
3. Select model: `agno/store-manager`
4. Ask test questions from this document
5. Verify responses against success criteria

---

## Test Coverage Summary

| Use Case | Unit Tests | Manual Questions | Jira Integration |
|----------|-----------|------------------|------------------|
| 1. Discovery & Availability | ✅ | 8 questions | ✅ |
| 2. Migration & Building | ✅ | 6 questions | ✅ |
| 3. Certification | ✅ | 6 questions | ✅ |
| 4. Lifecycle & Maintenance | ✅ | 9 questions | ✅ |
| 5. Support Boundaries | ✅ | 7 questions | ❌ |
| 6. Release Planning | ✅ | 8 questions | ✅ |
| 7. Metadata & Registry | ✅ | 7 questions | ❌ |
| 8. Team Coordination | ✅ | 7 questions | ✅ |
| **Total** | **8 test classes** | **58+ questions** | **6 use cases** |
