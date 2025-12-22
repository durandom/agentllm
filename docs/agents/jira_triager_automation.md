# Jira Triager: Automation Guide

## Overview

Automated Jira ticket triage runs on GitHub Actions schedule (weekdays at 6am EST):

- **Auto-triages** untriaged tickets using AI recommendations
- **Auto-applies** all AI-recommended updates
- **Slack notifications** with detailed results (ticket IDs, teams, components)
- **No artifacts** - all data stays confidential in workflow run

**How It Works:**

```
GitHub Actions (Weekdays at 6am EST)
         ↓
Load config from: github.com/JessicaJHee/rhdh-jira-triager-knowledge
         ↓
Query Jira for untriaged tickets (empty team/component)
         ↓
AI analyzes each ticket → Generate recommendations
         ↓
Auto-apply all recommendations (agent controls via SKIP/NEW actions)
         ↓
Send Slack notification with team/component details (encrypted HTTPS, private channel)
```

## Security & Privacy

The automation is designed to protect sensitive information even in public repositories:

- **No artifacts**: Results are never uploaded as artifacts - all data stays ephemeral within the workflow run
- **Slack notifications**: Sent via encrypted HTTPS to your private Slack channel
  - Contains full details: ticket IDs, teams, components
  - Sensitive data never appears in workflow logs (Python script approach)
- **Workflow logs**: Only contain non-sensitive execution details (no ticket titles, teams, or components)
- **Ephemeral data**: `results.json` is created on the runner's private filesystem and automatically deleted when the runner is destroyed
  - Not accessible to the public (even in public repos)
  - Contents never printed to workflow logs (only extracted counts appear as numbers)

**Security Model:**
- ✅ Safe for **public repositories** - sensitive data only visible in private Slack channel
- ✅ Slack webhook URL masked in logs (GitHub Secret)
- ✅ Ticket details sent directly to Slack, never exposed in public logs
- ✅ No persistent artifacts that could leak information

## Prerequisites

### 1. Team Configuration

The automation reads team mappings from a **private GitHub repository**:

```
https://github.com/JessicaJHee/rhdh-jira-triager-knowledge/blob/main/rhdh-teams.json
```

This file contains team IDs, components, and members. The workflow automatically checks out this repo during execution (no manual setup needed).

### 2. GitHub Secrets

Add these secrets to your repository (**Settings → Secrets and variables → Actions**):

| Secret | Description | Required |
|--------|-------------|----------|
| `JIRA_API_TOKEN` | Jira API token from issues.redhat.com | ✅ Yes |
| `GEMINI_API_KEY` | Gemini API key for AI analysis | ✅ Yes |
| `GH_PRIVATE_REPO_TOKEN` | GitHub PAT with `repo` scope for config access | ✅ Yes |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | ⚠️ Optional |

**To create `GH_PRIVATE_REPO_TOKEN`:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Set expiration (90 days recommended)
4. Check **`repo`** scope (Full control of private repositories)
5. Generate token and copy it
6. Add to repository secrets: Settings → Secrets and variables → Actions → New repository secret

**To get a Jira API token:**
1. Go to https://issues.redhat.com
2. Profile icon → Account Settings → Security → API Tokens
3. Create and copy token

**Hardcoded settings** (no configuration needed):
- Jira Server: `https://issues.redhat.com`
- Automation User: `jira-triager-bot`
- Config Location: `github.com/JessicaJHee/rhdh-jira-triager-knowledge`
- Default Filter: Untriaged tickets in RHIDP/RHDH projects

## Configuration

### Default Filter

The automation processes tickets matching:
- Projects: RHIDP, RHDH Support, RHDH Bugs
- Status: Not closed
- Missing: Team OR Component
- Excludes: Sub-tasks, Features, Outcomes

**Default JQL:**
```
project in ("Red Hat Internal Developer Platform", "RHDH Support", "Red Hat Developer Hub Bugs")
AND status != closed
AND (Team is EMPTY OR component is EMPTY)
AND issuetype not in (Sub-task, Feature, "Feature Request", Outcome)
ORDER BY created DESC, priority DESC
```

### Custom JQL Filters

You can override the default filter via manual workflow trigger.

## Usage

### Scheduled Runs (Automatic)

The workflow runs **automatically every weekday at 6am EST** (11am UTC, Monday-Friday).

No action required - just monitor Slack notifications.

### Manual Trigger

To run the automation manually:

1. Go to **Actions → Jira Auto-Triage → Run workflow**
2. Optional settings:
   - **Dry-run mode**: Preview recommendations without applying (sends Slack notification with "Would Assign" preview)
   - **Custom JQL filter**: Override the default filter to triage specific tickets
     - Example: `project = RHIDP AND status = "To Do" AND created >= -7d`
     - Leave empty to use the default filter (all untriaged tickets)
3. Click **Run workflow**

### Adjusting Schedule

Edit `.github/workflows/jira-auto-triage.yml` to change the schedule:

```yaml
# Scheduled run once daily at 6am EST (11am UTC), weekdays only
schedule:
  - cron: "0 11 * * 1-5"  # Monday-Friday at 6am EST / 11am UTC
```

## Monitoring

### Slack Notifications

Each run sends a Slack notification with:

- **Total Processed**: Number of unique issues analyzed
- **Would Assign / Successfully Assigned**: Number of issues updated (or would be updated in dry-run)
- **Ticket details**: Clickable links to Jira with team and component assignments
- **Failed updates** (if any): Tickets that failed to update
- **Workflow link**: Direct link to GitHub Actions run

**Dry-Run Mode Example:**
```
📊 Jira Auto-Triage Summary (Dry-Run)

Total Processed: 5
Would Assign: 5

🔍 Would Assign:
Plugin test failing  → Component: Plugin A
API connection timeout  → Team: Backend Team | Component: API Gateway
User reports login issue  → Team: Auth Team
Database query error  → Team: Backend Team
Permission settings not working  → Team: Security Team | Component: Auth Provider

View Workflow Run
```
*Note: Ticket titles are clickable links to Jira issues*

**Apply Mode Example:**
```
📊 Jira Auto-Triage Summary

Total Processed: 4
Successfully Assigned: 3

✅ Assigned Issues:
Plugin test failing  → Component: Plugin A
API connection timeout  → Team: Backend Team | Component: API Gateway
User reports login issue  → Team: Auth Team

⚠️ Failed to Update (1):
Database query error  → Team: Backend Team

View Workflow Run
```
*Note: Ticket titles are clickable links to Jira issues*

**Security Note:** Slack notifications are sent via encrypted HTTPS directly to your private Slack channel. Sensitive details (team names, component names) never appear in public workflow logs.

## Troubleshooting

### Missing Secrets Error

Add `JIRA_API_TOKEN` and `GEMINI_API_KEY` to repository secrets (Settings → Secrets and variables → Actions).

### Failed Updates

Check the workflow logs for error details. Common causes:
- Invalid team IDs in config
- Jira API permissions
- Network issues

### Config File Not Found

Ensure the private repo `JessicaJHee/rhdh-jira-triager-knowledge` is accessible and contains `rhdh-teams.json`.

## Best Practices

### Initial Setup

1. **Start with dry-run**: Test for 1-2 weeks before enabling auto-apply
2. **Monitor Slack**: Review notifications to understand patterns
3. **Update config**: Add missing component mappings as needed

### Ongoing Maintenance

1. **Update team config**: When team structure changes, update `rhdh-teams.json` in the config repo
2. **Monitor results**: Review Slack notifications for accuracy and patterns
3. **Rotate tokens**: Refresh Jira API token every 6-12 months
4. **Monitor failures**: Investigate failed updates via workflow logs

## Updating Team Configuration

To update team mappings when your team structure changes:

1. Go to https://github.com/JessicaJHee/rhdh-jira-triager-knowledge
2. Edit `rhdh-teams.json`
3. Commit changes to main branch
4. Next automation run will use updated config automatically

No code changes or redeployment needed!
