# Prompts Sheet Refactoring

**Date**: 2026-02-01
**Objective**: Eliminate duplication between hardcoded prompt and Excel workbook prompts

## Problem

The Release Manager had significant overlap between:
1. **Hardcoded prompt** in `release_manager_configurator.py`
2. **System prompt** in Excel Prompts sheet
3. **Situational prompts** that duplicated workflow instructions

This created:
- Maintenance burden (updating same content in multiple places)
- Confusion about source of truth
- Token waste (loading redundant guidance)

## Solution

### Principle: **Hardcoded Prompt = Primary, Excel = Supplementary**

The hardcoded prompt in `release_manager_configurator.py` remains the **authoritative source** for:
- Agent identity and core responsibilities
- Behavioral guidelines
- Configuration values injection
- Workflow enforcement framework
- Reference data (available queries, templates, workflows)

The Excel Prompts sheet now contains **only**:
- Concise system prompt with example questions
- Cross-cutting situational prompts (not covered by workflows)

## Changes Made

### Removed (3 prompts)

**Deleted due to overlap with Workflows:**

1. ❌ `feature_freeze_prep` - Duplicated "Announce Feature Freeze Update" workflow
2. ❌ `code_freeze_prep` - Duplicated "Announce Code Freeze Update" workflow
3. ❌ `release_status_check` - General guidance covered in hardcoded prompt

### Kept (2 prompts)

**Preserved as cross-cutting concerns:**

1. ✅ `risk_identification` - Applies to many workflows (code freeze, feature freeze, release status)
2. ✅ `team_coordination` - Applies to any team communication task

### Updated (1 prompt)

**Refactored system_prompt:**

**Before** (1,047 chars):
- Verbose identity statement
- Tool listings (redundant with toolkit registration)
- General guidance (redundant with hardcoded prompt)

**After** (756 chars):
```
You are the Release Manager for Red Hat Developer Hub (RHDH).

**Core Capabilities:**
- Query workbook for JQL templates, Slack templates, and workflows
- Execute Jira queries for release tracking
- Access Google Drive documents (team data, release schedules)
- Generate Slack announcements following templates

**Example Questions You Can Answer:**
[9 example questions from test scenarios]

**Key Principles:**
- Always use get_issues_by_team() for team counts
- Include Jira search links for traceability
- Format Slack announcements in Markdown code blocks
- Prioritize accuracy and data-driven insights
```

**Key improvement**: Now focuses on **example questions** to guide users, rather than repeating identity/capabilities already in hardcoded prompt.

## Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total prompts | 6 | 3 | **-50%** |
| System prompt chars | 1,047 | 756 | **-28%** |
| Situational prompts | 5 | 2 | **-60%** |
| Workflow duplication | 2 | 0 | **✅ Eliminated** |

## Architecture After Refactoring

```
┌─────────────────────────────────────────────────────────┐
│ Hardcoded Prompt (release_manager_configurator.py)     │
│ - Agent identity & core responsibilities               │
│ - Configuration values from workbook                   │
│ - Workflow enforcement framework                       │
│ - Reference data (queries, templates, workflows)       │
│ - Situational prompts reference list                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Excel Prompts Sheet (SUPPLEMENTARY)                     │
├─────────────────────────────────────────────────────────┤
│ system_prompt (injected into hardcoded prompt)          │
│ - Example questions from test scenarios                │
│ - Key principles (brief reminders)                     │
├─────────────────────────────────────────────────────────┤
│ Situational Prompts (on-demand via get_prompt())       │
│ - risk_identification (cross-cutting)                  │
│ - team_coordination (cross-cutting)                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Actions & Workflows Sheet                               │
│ - Prescriptive step-by-step recipes                    │
│ - Task-specific guidance (Feature Freeze, Code Freeze) │
│ - No duplication with prompts                          │
└─────────────────────────────────────────────────────────┘
```

## Benefits

1. **Single Source of Truth**: Hardcoded prompt is authoritative for agent identity
2. **No Duplication**: Removed workflow overlaps (feature_freeze_prep, code_freeze_prep)
3. **Token Efficiency**: 50% reduction in Excel prompts reduces workbook load time
4. **Clear Separation**:
   - Hardcoded = Static framework and enforcement
   - Excel system_prompt = Dynamic examples and current guidance
   - Excel situational = Cross-cutting best practices
   - Workflows = Task-specific recipes
5. **Maintainability**: Changes to agent identity happen in one place (code)
6. **Flexibility**: Example questions can be updated in Excel without code changes

## Testing

Verify the changes work correctly:

```bash
# Run all Release Manager scenarios
just rm-test all

# Check specific scenarios
just rm-test 20  # Code freeze announcement (should still work)
just rm-test 22  # Feature Freeze announcement (should still work)
just rm-test 24  # Risk analysis (should use risk_identification prompt)
```

## Migration Notes

- ✅ No code changes required (toolkit methods remain the same)
- ✅ Exported updated CSV: `exports/release manager_sheets/Prompts.csv`
- ✅ Updated Excel: `RHDH_Release_Manager_Reference.xlsx`
- ⚠️ If you added custom prompts to the workbook, review if they overlap with workflows

## Future Additions

When adding new prompts to the Excel sheet, ask:

1. **Is this covered by a workflow?** → Don't add, enhance the workflow instead
2. **Is this agent identity/behavior?** → Don't add, update hardcoded prompt instead
3. **Is this cross-cutting guidance?** → ✅ Add as situational prompt
4. **Is this example usage?** → ✅ Add to system_prompt example questions

---

**Result**: Clean separation of concerns, no duplication, easier maintenance! 🎯
