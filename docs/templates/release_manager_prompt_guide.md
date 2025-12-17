# Release Manager Prompt Maintenance Guide

This guide is for release managers, team leads, and anyone maintaining the Release Manager agent's extended system prompt.

## Overview

The Release Manager uses a **dual-prompt architecture**:

1. **Embedded System Prompt** (in code) - Agent's core identity and capabilities
2. **Extended System Prompt** (in Google Doc) - Operational instructions you maintain

**You maintain the Extended System Prompt.** This guide shows you how.

## What Goes in the Extended Prompt

### ✅ DO Include

**Jira Query Patterns:**
```
project = RHDH AND fixVersion = "{RELEASE_VERSION}" ORDER BY priority DESC
```
- Reusable templates with placeholders
- Team-specific JQL queries
- Custom field queries

**Response Instructions:**
- "When user asks X, query Y, format as Z"
- How to prioritize information
- What context to include
- Formatting guidelines

**Communication Guidelines:**
- Slack channels for different purposes
- When to escalate
- Meeting formats and agendas

**Process Workflows:**
- Your team's release process steps
- Timelines and milestones
- Risk identification patterns

**Team-Specific Information:**
- Google Drive folder locations
- Confluence page URLs
- Dashboard links
- Team contact information

### ❌ DO NOT Include

**Hardcoded Release Data:**
```
Bad:  "Release 1.5.0 is scheduled for 2025-01-15"
Good: "Query Jira for upcoming releases and their dates"
```

**User Documentation:**
```
Bad:  "Welcome to Release Manager! Here's how to use me..."
Good: "When user asks about status, query Jira and summarize..."
```

**Agent Capabilities:**
```
Bad:  "I can access Google Drive and Jira..."
Good: "Use Google Drive tools to fetch release calendar..."
```
These belong in the embedded prompt (code), not here.

---

## Prompt Engineering Best Practices

Before you start customizing, understand these core principles. They'll help you write effective, maintainable prompts.

### Principle 1: Explicit Tool Mapping

**Problem:** Abstract action names force the LLM to guess which tool to use.

**Bad:**
```markdown
When user asks about team issues, run **Retrieve Issues by Team** for each team.
```

**Good:**
```markdown
When user asks about team issues, use `get_issues_by_team(release_version, team_ids)` for accurate per-team counts.
```

**Why:** The agent knows exactly which function to call and what parameters it needs. No inference required.

**Action:** Always use actual function names like `get_issue()`, `get_issues_by_team()`, `get_document_content()` instead of abstract descriptions.

---

### Principle 2: DRY (Don't Repeat Yourself)

**Problem:** Duplication wastes tokens and creates ambiguity.

**Bad:**
```markdown
## Query for Feature Freeze
project IN (RHIDP, RHDHBugs) AND fixVersion = "X" and status != closed

## Query for Code Freeze
project IN (RHIDP, RHDHBugs) AND fixVersion = "X" and status != closed

## Query for Open Issues
project IN (RHIDP, RHDHBugs) AND fixVersion = "X" and status != closed
```

**Good:**
```markdown
## Query for Open Issues
project IN (RHIDP, RHDHBugs) AND fixVersion = "[RELEASE_VERSION]" and status != closed

Note: Use this query for all freeze milestones (Feature, Code, Doc)
```

**Why:** Each token counts toward context limits. Duplication = wasted space.

**Action:** Define concepts once, reference them elsewhere. Remove TODO sections and empty placeholders.

---

### Principle 3: Conciseness - Assume the LLM is Smart

**Problem:** Verbose meta-instructions about "how to think" waste tokens.

**Bad:**
```markdown
Before retrieving data:
1. Identify the data sources required for this action
2. If multiple sources exist:
   - Announce: "This action requires [Source A] (primary)..."
   - Commit: "I will check [Source A] FIRST..."
3. Execute in priority order...
```

**Good:**
```markdown
Data Sources (priority order):
1. Jira (primary) - Use `get_issue()` for release dates
2. Spreadsheet (fallback) - Only if Jira lacks dates
```

**Why:** Modern LLMs already know how to reason step-by-step. Don't teach them HOW to think, just WHAT to produce.

**Action:** Remove instructions like "announce your findings," "commit to checking X first," "verify before accessing Y." The agent does this naturally.

---

### Principle 4: Outcome-Focused Instructions

**Problem:** Procedural "do-this-then-that" steps constrain the agent's path-finding.

**Bad:**
```markdown
📋 First, gather the data:
| Step | What to Do | What You'll Get |
| 1 | Run Retrieve Release Dates | Feature Freeze date |
| 2 | Run Retrieve Teams | List of teams |
| 3 | For each team, run Retrieve Issues | Counts |

▶️ Then, fill in the template:
```

**Good:**
```markdown
**Output:** Slack message announcing Feature Freeze status

**Data Requirements:**
1. Feature Freeze date - Use `get_issue(RHDHPLAN-XXX)`
2. Active engineering teams - Use `get_document_content("DOC_ID")`
3. Team issue counts - Use `get_issues_by_team(version, ids)`

**Template:**
[actual template here]
```

**Why:** Lead with the destination (desired output), not the journey (procedure). Agents are excellent pathfinders - give them the goal and they'll optimize the route.

**Action:** Structure instructions as `Output → Data Requirements → Template`, not `Step 1 → Step 2 → Step 3 → Output`.

---

### Principle 5: Format Targeting (Destination + Delivery Method)

**Problem:** Output format must match BOTH the platform AND how it's delivered.

**Critical Discovery:** Slack has TWO formatting systems:
- **mrkdwn** (API/webhooks): `<url|text>` for links, `*bold*`
- **Markdown** (manual paste): `[text](url)` for links, `*bold*`

**Bad (assumes API):**
```markdown
• *Team* - <https://jira.com/...|71> @Lead
```
This ONLY works via API/webhooks, NOT manual pasting!

**Good (for copy-paste):**
```markdown
• *Team* - [71](https://jira.com/...) @Lead
```
This works when pasting into Slack manually.

**Why:** The `<url|text>` syntax fails when manually pasted. Users see raw angle brackets instead of links.

**Action:**
- For copy-paste workflows → Use Markdown: `[text](url)`
- For API/webhook workflows → Use mrkdwn: `<url|text>`
- Match format to delivery method, not just destination platform

**Slack Formatting Reference:**
| Format | Markdown (paste) | mrkdwn (API) |
|--------|-----------------|--------------|
| Bold | `*text*` | `*text*` |
| Link | `[text](url)` | `<url\|text>` |
| Link count | `[71](url)` | `<url\|71>` |

---

### Common Pitfalls to Avoid

**1. Empty Section Placeholders**
```markdown
❌ ## Announce Code Freeze

    (no content - TODO)
```
Remove empty sections. They waste tokens and create confusion.

**2. Mixing Formatting Syntaxes**
```markdown
❌ *RHDH 1.9.0 <url|Feature Freeze> Update*
   (mixing Markdown bold with mrkdwn link)
```
Pick ONE syntax and use it consistently.

**3. Triple-Duplicated Queries**
```markdown
❌ Same JQL query repeated under three different section names
```
Define once, reference elsewhere.

**4. Meta-Commentary About Thinking**
```markdown
❌ "Think carefully about whether Jira has the dates before checking the spreadsheet"
```
State the constraint, trust the agent to reason.

**5. Abstract Action Names Without Tool Mapping**
```markdown
❌ "Run Retrieve Issues by Team"
✅ "Use get_issues_by_team(release_version, team_ids)"
```

---

### Quick Self-Audit Checklist

Before deploying prompt changes, verify:

- [ ] **Tool mapping** - All actions use actual function names (`get_issue()`)
- [ ] **No duplication** - Each JQL query defined once
- [ ] **Concise** - No meta-instructions about how to think
- [ ] **Outcome-first** - Instructions lead with desired output
- [ ] **Format consistency** - One syntax (Markdown OR mrkdwn), not mixed
- [ ] **No empty sections** - Remove TODO placeholders
- [ ] **Tested** - Verified with actual agent before deploying

---

## Getting Started

### Initial Setup

1. **Open the template:**
   - File: `docs/templates/release_manager_system_prompt.md`
   - This is your starting point

2. **Create Google Doc:**
   - Go to [Google Drive](https://drive.google.com)
   - Click "New" > "Google Docs"
   - Title it: "Release Manager System Prompt - [Your Team]"

3. **Copy content:**
   - Copy ALL content from the template file
   - Paste into your new Google Doc
   - **Keep the markdown formatting as plain text** (see Working with Markdown below)

4. **Customize for your team:**
   - Update Jira project key (`RHDH` → your project)
   - Update Slack channel names
   - Update process timelines
   - Add team-specific queries

5. **Share the document:**
   - Click "Share" button
   - Set sharing to:
     - "Anyone with the link can view" (if public)
     - Or add specific users/groups (if private)
   - Copy the document URL and share with technical team for configuration

---

## Working with Markdown in Google Docs

**Important:** The agent reads the Google Doc as **plain text**, not formatted text. You must write in Markdown syntax, even though Google Docs displays it as unformatted text.

### What is Markdown?

Markdown is a simple text formatting syntax. Instead of using Google Docs' formatting toolbar, you write special characters that the agent interprets:

```
# This becomes a heading
**This becomes bold**
[This becomes a link](https://example.com)
```

### Key Markdown Syntax

**Headings:**
```markdown
# Heading 1
## Heading 2
### Heading 3
```

**Bold and Emphasis:**
```markdown
*single asterisk for italic*
**double asterisk for bold**
```

**Links:**
```markdown
[Link text](https://url.com)
```

**Lists:**
```markdown
- Bullet point
- Another bullet point

1. Numbered item
2. Another numbered item
```

**Code Blocks:**
```markdown
\`\`\`
Code goes here
Multiple lines supported
\`\`\`
```

**Inline Code:**
```markdown
Use `backticks` for inline code like function names
```

### Critical: Don't Use Google Docs Formatting

❌ **DON'T:**
- Use Google Docs' "Bold" button (Ctrl+B / Cmd+B)
- Use Google Docs' heading styles dropdown
- Use "Insert → Link" menu
- Use "Format → Paragraph styles"

✅ **DO:**
- Type Markdown syntax manually as plain text
- Use `**bold**` instead of clicking Bold button
- Use `[link](url)` instead of Insert → Link
- Use `#` for headings instead of style dropdown

### Why This Matters

When you click Google Docs' "Bold" button:
- **You see:** Bold text in the document
- **Agent sees:** Regular text (no asterisks)
- **Result:** Agent can't detect the formatting ❌

When you type `**bold**` as text:
- **You see:** Literal `**bold**` in the document
- **Agent sees:** `**bold**` (understands this means bold)
- **Result:** Agent correctly interprets formatting ✅

### Practical Example

**Wrong approach (using Google Docs formatting):**

```
[What you type in Google Docs with Ctrl+B applied]
Release 1.5.0 Status

[What agent sees]
Release 1.5.0 Status   ← No heading marker!
```

**Correct approach (using Markdown):**

```
[What you type in Google Docs as plain text]
## Release 1.5.0 Status

[What agent sees]
## Release 1.5.0 Status   ← Agent understands this is a heading!
```

### Tips for Working in Google Docs

1. **Use monospace font (optional but helpful):**
   - Select all text (Ctrl+A / Cmd+A)
   - Font → "Courier New" or "Roboto Mono"
   - This makes Markdown syntax easier to read

2. **Turn off auto-formatting:**
   - Tools → Preferences
   - Uncheck "Use smart quotes"
   - Uncheck "Automatic substitution"

3. **Preview your Markdown:**
   - Copy a section
   - Paste into a Markdown preview tool (e.g., https://markdownlivepreview.com/)
   - Verify formatting looks correct

4. **Keep a reference open:**
   - Keep the template file open in a second tab
   - Copy formatting patterns from template
   - Ensures consistency

### Common Mistakes

**Mistake 1: Mixing Markdown and Google Docs formatting**
```
❌ **Bold text** with <Google Docs bold applied to different text>
✅ **Bold text** all in Markdown
```

**Mistake 2: Not escaping special characters**
```
❌ Use * for multiplication  (Markdown thinks this is italic)
✅ Use \* for multiplication  (Backslash escapes the asterisk)
```

**Mistake 3: Forgetting code blocks**
```
❌ project = RHDH AND fixVersion = "1.5.0"
   (Agent might interpret = as Markdown)

✅ ```
   project = RHDH AND fixVersion = "1.5.0"
   ```
   (Code block protects special characters)
```

### Quick Reference Card

Save this in your Google Doc as a comment or separate section:

```markdown
# Heading 1        ## Heading 2        ### Heading 3
*italic*           **bold**             `code`
[link](url)        - bullet list       1. numbered list

Code block:
\`\`\`
code here
\`\`\`
```

## Making Updates

### When to Update

Update the prompt when:
- **Process changes** - New release workflow, different timelines
- **Jira structure changes** - New custom fields, different project keys
- **Communication changes** - New Slack channels, different escalation paths
- **Query patterns change** - Better JQL queries discovered
- **Feedback from users** - Agent not responding as expected

### How to Update

1. **Edit the Google Doc directly:**
   - Open your Google Doc
   - Make changes using Markdown syntax (see "Working with Markdown" section)
   - Save automatically (Google Docs saves as you type)

2. **Changes take effect:**
   - Changes are live immediately in the Google Doc
   - The agent will use updated content when it refreshes
   - Coordinate with your technical team if changes need immediate application

### Testing Updates

**Best Practice: Use a Dev Copy**

1. **Create dev copy:**
   - In Google Drive, right-click your production doc
   - Select "Make a copy"
   - Name it: "Release Manager System Prompt - DEV"

2. **Make and test changes:**
   - Edit the dev doc with your proposed changes
   - Share dev doc URL with technical team for testing
   - Ask technical team to verify agent behavior with dev doc

3. **Deploy to production:**
   - Once testing confirms changes work correctly
   - Copy the updated content from dev doc to production doc
   - Production agent will use new content on next refresh

**Quick Edits (for minor changes):**

If you're fixing typos or updating dates:
1. Edit production doc directly
2. Changes are live immediately
3. Monitor agent responses to ensure no issues

## Customization Examples

### Example 1: Add New Jira Query

**Scenario:** You want to track documentation tickets separately.

**Add to "Jira Query Patterns" section:**

```markdown
### Documentation Tickets

**Query Purpose:** Find all documentation tickets for a release

**JQL:**
\```
project = RHDH AND fixVersion = "{RELEASE_VERSION}" AND labels = "documentation" ORDER BY status
\```

**Example:**
\```
project = RHDH AND fixVersion = "1.5.0" AND labels = "documentation" ORDER BY status
\```
```

### Example 2: Update Slack Channels

**Scenario:** Your team reorganized Slack channels.

**Update "Communication Guidelines" section:**

```markdown
### Slack Channels

**Release Announcements:**
- Channel: `#releases-public`  ← Changed from #rhdh-releases
- When: Major milestones, release candidates, final releases

**Internal Discussions:**
- Channel: `#dev-releases-internal`  ← Changed from #rhdh-dev
- When: Daily updates, blocker discussions
```

### Example 3: Add Custom Response Instruction

**Scenario:** Users often ask about specific feature status.

**Add to "Response Instructions" section:**

```markdown
### "Is feature X included in release Y.Z.W?"

**Actions:**
1. Query Jira:
   \```
   project = RHDH AND fixVersion = "Y.Z.W" AND summary ~ "feature-name"
   \```
2. Check ticket status
3. If Done: Confirm inclusion with ticket link
4. If In Progress: Provide status and ETA
5. If Not Found: Search without fixVersion filter

**Response Format:**
\```markdown
**Feature Status for Release Y.Z.W:**

- [JIRA-123] Feature Name
- Status: Done / In Progress / Planned
- Details: [Brief description]
- [Link to ticket]
\```
```

### Example 4: Adjust Release Timeline

**Scenario:** Your team moved to shorter release cycles.

**Update "Process Workflows" → "Y-Stream Release Process":**

```markdown
1. **Planning Phase** (1 week before code freeze)  ← Changed from 2-3 weeks
   - Define scope and features
   ...

2. **Development Phase** (2-3 weeks)  ← Changed from 4-6 weeks
   - Regular progress checks
   ...
```

## Best Practices

### Writing Effective Instructions

**Be Specific:**
```
Bad:  "Help users with releases"
Good: "When user asks for release status, query Jira for fixVersion tickets,
       group by status, identify blockers, and provide completion percentage"
```

**Use Examples:**
```
When describing a format, always provide an example:

**Response Format:**
\```markdown
## Release 1.5.0 Status
**Progress:** 75% complete
...
\```
```

**Think Like an Agent:**
```
Bad:  "Users should check Jira for status"
Good: "Query Jira for status and present to user"
```

You're instructing the agent, not the user.

### Maintenance Schedule

**Monthly Review:**
- Verify Jira queries still work
- Check if Slack channels are current
- Review recent agent interactions for issues
- Update any outdated information

**After Process Changes:**
- Update workflow sections immediately
- Test with real scenarios
- Update examples to match new process

**After Major Releases:**
- Conduct retrospective on agent performance
- Gather feedback from team
- Identify improvements needed
- Update prompt accordingly

### Version Control

**Track Changes:**

Add to bottom of Google Doc:

```markdown
---
## Change Log

**2025-01-15:**
- Updated Y-stream timeline to 2-3 weeks
- Added new Jira query for documentation tickets
- Changed Slack channel names

**2024-12-20:**
- Added risk identification section
- Updated escalation triggers
- Initial version deployed
```

**Collaborative Editing:**

If multiple people maintain the prompt:

1. Assign sections to owners
2. Use Google Doc comments for discussions
3. Review changes before deploying to production
4. Communicate updates to team

## Troubleshooting

### Agent Not Using My Instructions

**Issue:** Agent doesn't follow the extended prompt

**What You Can Check:**

1. **Verify document sharing:**
   - Open your Google Doc
   - Click "Share" button
   - Ensure "Anyone with the link can view" is enabled
   - OR ensure specific technical team members have access

2. **Check instructions clarity:**
   - Review your wording for ambiguity
   - Add more specific examples
   - Use concrete function names (e.g., `get_issue()`)
   - Follow the "Quick Self-Audit Checklist" above

3. **Contact technical team:**
   - Share the specific agent behavior you're seeing
   - Provide the doc URL
   - Ask them to verify the agent is reading your doc

### Document Permission Issues

**Symptom:** Technical team reports "Failed to fetch extended system prompt"

**What You Can Do:**

1. **Fix sharing settings:**
   - Open Google Doc
   - Click "Share" button
   - Change to "Anyone with the link can view"
   - OR add the service account email provided by technical team

2. **Verify you're sharing the right link:**
   - Copy the document URL from your browser
   - It should look like: `https://docs.google.com/document/d/LONG_ID_HERE/edit`
   - Share this exact URL with technical team

### Changes Not Appearing

**Issue:** You updated the doc but agent still uses old instructions

**What You Can Do:**

1. **Verify you're editing the right doc:**
   - Ask technical team which doc URL is configured
   - Open that doc and confirm it has your changes
   - Check you're not accidentally editing a copy

2. **Check for Markdown errors:**
   - Copy a section of your doc
   - Paste into https://markdownlivepreview.com/
   - Verify formatting renders correctly
   - Fix any syntax errors

3. **Request cache refresh:**
   - Contact technical team
   - Ask them to refresh the agent's cache
   - Provide doc URL and what you changed

## FAQ

**Q: Can I use Google Docs formatting (bold, headings, etc.)?**

A: No! You must use Markdown syntax. The agent reads raw text, not formatting. Click **Bold** in Google Docs and the agent sees nothing. Type `**bold**` as text and the agent understands it. See "Working with Markdown in Google Docs" section.

**Q: How do I make headings?**

A: Type `#` symbols as text:
- `# Heading 1` (one hash)
- `## Heading 2` (two hashes)
- `### Heading 3` (three hashes)

Don't use Google Docs' "Heading" style dropdown!

**Q: How do I make links?**

A: Type `[link text](https://url.com)` as plain text. Don't use Google Docs "Insert → Link" menu. The agent reads the Markdown syntax `[...](..)`, not Google Docs hyperlinks.

**Q: Can I include code (like JQL queries)?**

A: Yes! Use triple backticks for code blocks:
```
\`\`\`
project = RHDH AND fixVersion = "1.5.0"
\`\`\`
```
This protects special characters from being interpreted as Markdown.

**Q: How large can the prompt be?**

A: Keep it concise - aim for under 10KB (roughly 20-30 Google Docs pages). Long prompts can slow agent responses and reduce quality. Follow the "Conciseness" principle.

**Q: What if I want different instructions for different users?**

A: The prompt is shared by all users. Everyone using the agent sees the same instructions. For user-specific behavior, contact your technical team.

**Q: Can I test changes before they go live?**

A: Yes! Make a copy of the production doc, edit the copy, and share it with your technical team for testing. Once verified, copy the changes to the production doc.

**Q: Do my changes take effect immediately?**

A: Changes are saved immediately in Google Docs, but the agent may cache the prompt. For important changes, notify your technical team so they can refresh the cache.

## Getting Help

**For Prompt Content Questions:**
- Test Jira queries manually in Jira first
- Use Markdown preview tool to verify formatting: https://markdownlivepreview.com/
- Review the "Quick Self-Audit Checklist" above
- Get feedback from team members who use the agent

**For Technical Issues:**
- Contact your technical team
- Provide: doc URL, what you changed, and what behavior you're seeing
- They can check logs and configuration

## Summary Checklist

When maintaining the prompt:

**Content Quality:**
- [ ] Instructions are clear and specific
- [ ] Jira queries tested manually in Jira first
- [ ] Slack channels are current
- [ ] Process timelines match reality
- [ ] Examples provided for complex formats
- [ ] No hardcoded release data
- [ ] Written for agent, not users

**Markdown Formatting:**
- [ ] Used `**bold**` syntax (not Google Docs Bold button)
- [ ] Used `[text](url)` for links (not Insert → Link)
- [ ] Used `#` `##` `###` for headings (not Heading styles)
- [ ] Code blocks wrapped in triple backticks (\`\`\`)
- [ ] Previewed in https://markdownlivepreview.com/

**Best Practices:**
- [ ] Followed "Quick Self-Audit Checklist" (7 points above)
- [ ] No duplicate queries or empty sections
- [ ] Used actual function names (`get_issue()`)
- [ ] Outcome-focused structure (Output → Data → Template)

**Deployment:**
- [ ] Changes logged in document
- [ ] Tested in dev copy before production
- [ ] Team notified of updates
- [ ] Technical team contacted for cache refresh (if needed)

---

**Remember:** The extended prompt is a powerful tool for customizing agent behavior. Keep it concise, use Markdown correctly, test your changes, and iterate based on user feedback!
