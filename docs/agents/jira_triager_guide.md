# Jira Triager - User Guide

## Overview

Analyzes Jira tickets and recommends team/component assignments using component mappings, keyword analysis, and assignee validation.

## Quick Start

**Prerequisites**: Jira API token + Google Drive OAuth + `JIRA_TRIAGER_GDRIVE_FOLDER_ID` env var

**First Use**:
1. Provide Jira token: `my jira token is TOKEN_HERE and server is https://issues.redhat.com`
2. Authorize Google Drive (OAuth URL provided by agent)
3. Start triaging: `Triage RHIDP-8796`

## Usage

**Single ticket**: `Triage RHIDP-8796`
- Agent analyzes and shows recommendations
- Shows summary table with ticket
- Automation mode: Script controls application

**Batch triage**: `Triage all issues in queue`
- Agent finds all tickets from configured filter
- Processes ALL tickets first
- Shows ONE consolidated table with ALL tickets
- Automation mode: Script controls application

## Update Workflow

**Automation Mode (CronJob/Scripts):**
1. Agent analyzes all tickets
2. Shows reasoning for each decision
3. Outputs consolidated summary table
4. Script parses table and applies changes based on configuration

**Interactive Mode (Web UI):**
1. Agent analyzes ticket(s)
2. Shows recommendations and reasoning
3. Outputs summary table:
   ```
   | Ticket | Summary | Field | Current | Recommended | Confidence | Action |
   |--------|---------|-------|---------|-------------|------------|--------|
   | RHIDP-100 | Login fails | Team | (empty) | Security | 100% | NEW |
   |  |  | Components | Catalog | Catalog, Keycloak | 90% | APPEND |
   | RHIDP-101 | Operator crash | Team | Install | Already Set | - | SKIP |
   |  |  | Components | (empty) | Operator | 85% | NEW |
   ```
4. Updates are controlled by the calling environment (script or user)

**Action Codes:**
- NEW: Field is empty, will add new value
- APPEND: Will add additional components to existing ones (never replaces team)
- SKIP: Field already correct, no change

## Confidence Scores

- **100%**: Assignee found in team mapping (deterministic)
- **90-95%**: Strong logical match (issue domain clearly aligns with team)
- **75-85%**: Moderate match (issue relates to team's area)
- **60-70%**: Weak match (best guess)
- **<60%**: Ask for guidance

**Component Validation**: Agent validates recommended components exist in Jira project before suggesting.

## Configuration

**Automation Mode** (CronJob):
- `rhdh-teams.json` - Team config mounted as ConfigMap (IDs, components, members)
- System prompt embedded in code (`jira_triager_configurator.py` lines 96-217)

**Interactive Mode**:
- Google Drive folder (`JIRA_TRIAGER_GDRIVE_FOLDER_ID`):
  - `rhdh-teams.json` - Team config
  - `jira-filter.txt` - Default JQL filter (optional)

**rhdh-teams.json example**:
```json
{
  "RHIDP - Security": {
    "id": "4267",
    "components": ["Keycloak provider", "RBAC Plugin"],
    "members": ["Jessica He", "John Doe"]
  }
}
```

**Updating System Prompt**:
- Edit `src/agentllm/agents/jira_triager_configurator.py` lines 96-217
- Rebuild container: `make build-agentllm`
- Deploy new image

## Troubleshooting

- **No recommendation**: Add components or provide more context
- **Configuration not loaded**: Check `JIRA_TRIAGER_GDRIVE_FOLDER_ID` and folder permissions
- **Update failed**: Verify team ID in TEAM_ID_MAP
