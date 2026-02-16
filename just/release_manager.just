# Release Manager Test Recipes
#
# Run Release Manager scenario tests with easy scenario selection
# and workbook source toggling.

# ==============================================================================
# Release Manager Scenario Tests
# ==============================================================================

# Scenario metadata (keep in sync with tests/test_release_manager_scenarios.py)
# Updated: 2026-02-01 - 25 scenarios with expanded Level 1 (single-toolkit) tests
_scenarios := '
1   L1_01  "What Jira queries are available in the workbook?"
2   L1_02  "Show me the Feature Freeze Update template"
3   L1_03  "How many issues are open in fixVersion 1.9.0?"
4   L1_04  "Are there any blocker bugs in the 1.9 release?"
5   L1_05  "How do I generate a release status update?"
6   L1_06  "What are the Jira project keys used for tracking?"
7   L1_07  "Show me documentation for the get_issues_by_team tool"
8   L1_08  "Show me the feature_freeze_prep prompt"
9   L1_09  "List all available workflows in the workbook"
10  L1_10  "Get details for issue RHIDP-15779"
11  L1_11  "What fix versions exist in the RHIDP project?"
12  L1_12  "What sprint is issue RHIDP-15779 in?"
13  L1_13  "What are the key dates for active releases?"
14  L1_14  "What are the key dates for future releases from the release schedule spreadsheet?"
15  L1_15  "List all active RHDH teams with their leads and Slack handles"
16  L2_16  "Use the open_issues_by_type query template for version 1.9.0 with issuetype=Feature"
17  L2_17  "What is the status of release 1.9.0?"
18  L2_18  "What CVEs are outstanding for release 1.9.0?"
19  L2_19  "Get open issue counts by team for release 1.9.0"
20  L3_20  "Create a code freeze announcement for release 1.9.0"
21  L3_21  "Break down open issues by team for release 1.9.0"
22  L3_22  "Create a Feature Freeze Update announcement for release 1.9"
23  L4_23  "How many features are tagged for demos in version 1.9.0?"
24  L4_24  "What are the top 3 risks for releasing version 1.9.0 on time?"
25  L4_25  "Show me all features in release 1.9.0 that are still in progress"
'

# Run Release Manager scenario tests
# Usage:
#   just rm-test              # List all scenarios
#   just rm-test list         # List all scenarios
#   just rm-test all          # Run all scenarios (Google Drive)
#   just rm-test 5            # Run scenario 5 (Google Drive)
#   just rm-test 5 --local-sheets  # Run scenario 5 with local CSV sheets
#   just rm-test 5 --log      # Run scenario 5 with markdown logging
#   just rm-test level-1      # Run all Level 1 scenarios
rm-test *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    # Parse arguments
    scenario=""
    use_local_sheets=false
    enable_logging=false
    model_override=""

    for arg in {{ ARGS }}; do
        case "$arg" in
            --local-sheets|--local)
                use_local_sheets=true
                ;;
            --log|--logs)
                enable_logging=true
                ;;
            --model=*)
                model_override="${arg#*=}"
                ;;
            list|help)
                scenario="list"
                ;;
            all)
                scenario="all"
                ;;
            level-1|level-2|level-3|level-4)
                scenario="$arg"
                ;;
            [1-9]|1[0-9]|2[0-5])
                scenario="$arg"
                ;;
            *)
                echo "❌ Unknown argument: $arg"
                echo ""
                echo "Usage:"
                echo "  just rm-test                # List scenarios"
                echo "  just rm-test all            # Run all scenarios"
                echo "  just rm-test 5              # Run scenario 5"
                echo "  just rm-test 5 --local-sheets  # Use local CSV sheets"
                echo "  just rm-test 5 --log        # Run with markdown logging"
                echo "  just rm-test 5 --model=gemini-2.5-flash  # Use specific model"
                echo "  just rm-test level-1        # Run all Level 1 scenarios"
                exit 1
                ;;
        esac
    done

    # Default to list if no args
    if [ -z "$scenario" ]; then
        scenario="list"
    fi

    # List scenarios
    if [ "$scenario" = "list" ]; then
        echo ""
        echo "================================================================================"
        echo "📋 RELEASE MANAGER TEST SCENARIOS"
        echo "================================================================================"
        echo ""
        echo "Available scenarios:"
        echo ""

        # Parse and display scenarios
        echo '{{ _scenarios }}' | grep -v '^$' | while IFS= read -r line; do
            if [ -n "$line" ]; then
                num=$(echo "$line" | awk '{print $1}')
                level_id=$(echo "$line" | awk '{print $2}')
                desc=$(echo "$line" | cut -d'"' -f2)
                # Format with alignment
                printf "  %-3s %-7s  %s\n" "$num" "$level_id" "$desc"
            fi
        done

        echo ""
        echo "Levels:"
        echo "  L1: Single-Toolkit (basic queries, simple reasoning)"
        echo "  L2: Cross-Toolkit (combine data from multiple sources)"
        echo "  L3: Structured Workflows (multi-step processes with templates)"
        echo "  L4: Advanced Analysis (complex reasoning, risk analysis, accuracy)"
        echo ""
        echo "Usage:"
        echo "  just rm-test                # List scenarios"
        echo "  just rm-test all            # Run all scenarios"
        echo "  just rm-test 5              # Run scenario 5"
        echo "  just rm-test 5 --local-sheets  # Use local CSV sheets"
        echo "  just rm-test 5 --log        # Run with markdown logging (tmp/scenario_logs/)"
        echo "  just rm-test 5 --model=gemini-2.5-flash  # Use specific model"
        echo "  just rm-test level-1        # Run all Level 1 scenarios"
        echo "  just rm-test all --log      # Run all scenarios with logging"
        echo ""
        echo "Workbook Sources:"
        echo "  Default:        Google Drive (requires OAuth + RELEASE_MANAGER_WORKBOOK_GDRIVE_URL)"
        echo "  --local-sheets: Local CSV files (exports/release manager_sheets/)"
        echo ""
        echo "Models:"
        echo "  Default:               gemini-3-pro-preview (best for complex reasoning)"
        echo "  --model=<name>:        Override model (e.g., gemini-2.5-flash for speed)"
        echo "  Available models:      gemini-3-pro-preview, gemini-2.5-pro, gemini-2.5-flash"
        echo ""
        echo "Logging:"
        echo "  Default:  No markdown logs (faster)"
        echo "  --log:    Generate markdown logs in tmp/scenario_logs/"
        echo "            Includes: reasoning, tool calls, validation, metrics"
        echo ""
        echo "================================================================================"
        echo ""
        exit 0
    fi

    # Determine pytest arguments
    test_path="tests/test_release_manager_scenarios.py::TestReleaseManagerScenarios::test_scenario"
    pytest_args="-v -s -m integration"

    # Build scenario filter
    if [ "$scenario" = "all" ]; then
        # Run all scenarios (no filter)
        test_target="$test_path"
        echo ""
        echo "================================================================================"
        echo "🚀 RUNNING ALL RELEASE MANAGER SCENARIOS"
        echo "================================================================================"
    elif [[ "$scenario" =~ ^level-[1-4]$ ]]; then
        # Run all scenarios for a level
        level_num="${scenario#level-}"
        test_target="$test_path"
        # Filter by L1_, L2_, L3_, or L4_ prefix
        pytest_args="$pytest_args -k L${level_num}_"
        echo ""
        echo "================================================================================"
        echo "🚀 RUNNING LEVEL $level_num SCENARIOS"
        echo "================================================================================"
    else
        # Run specific scenario
        # Find the level_id for this scenario number
        level_id=$(echo '{{ _scenarios }}' | grep "^$scenario " | awk '{print $2}')
        if [ -z "$level_id" ]; then
            echo "❌ Scenario $scenario not found"
            exit 1
        fi

        # Use -k filter to match the level_id prefix (e.g., L1_01)
        test_target="$test_path"
        pytest_args="$pytest_args -k ${level_id}"

        echo ""
        echo "================================================================================"
        echo "🚀 RUNNING SCENARIO $scenario: $level_id"
        echo "================================================================================"
    fi

    # Display workbook source
    echo ""
    if [ "$use_local_sheets" = true ]; then
        echo "📄 Workbook Source: Local CSV sheets"
        echo "   (exports/release manager_sheets/)"
        export USE_LOCAL_SHEETS=true
    else
        echo "📄 Workbook Source: Google Drive"
        echo "   (requires OAuth + RELEASE_MANAGER_WORKBOOK_GDRIVE_URL env var)"
    fi

    # Display logging status
    if [ "$enable_logging" = true ]; then
        echo "📝 Markdown Logging: ENABLED"
        echo "   (logs will be saved to tmp/scenario_logs/)"
        export RELEASE_MANAGER_SCENARIO_LOGS=true
    else
        echo "📝 Markdown Logging: DISABLED"
        echo "   (use --log to enable)"
    fi

    # Display and set model override
    if [ -n "$model_override" ]; then
        echo "🤖 Model Override: $model_override"
        echo "   (via RELEASE_MANAGER_MODEL env var)"
        export RELEASE_MANAGER_MODEL="$model_override"
    else
        echo "🤖 Model: gemini-3-pro-preview (default)"
        echo "   (use --model=<name> to override)"
    fi

    echo ""
    echo "================================================================================"
    echo ""

    # Run the test
    uv run pytest "$test_target" $pytest_args

# List Release Manager scenarios (alias for rm-test)
rm-scenarios:
    @just rm-test list

# Run all Release Manager scenarios
rm-test-all:
    @just rm-test all

# Run all Release Manager scenarios with local CSV sheets
rm-test-all-local:
    @just rm-test all --local-sheets

# Run Release Manager scenario with markdown logging enabled
# Usage: just rm-test-log 5
rm-test-log SCENARIO *ARGS:
    @just rm-test {{ SCENARIO }} --log {{ ARGS }}

# Run all scenarios with markdown logging enabled
rm-test-all-log:
    @just rm-test all --log

# Run Level 1 scenarios with markdown logging enabled
rm-test-level1-log:
    @just rm-test level-1 --log

# View scenario logs index
rm-logs:
    #!/usr/bin/env bash
    if [ -f tmp/scenario_logs/index.md ]; then
        cat tmp/scenario_logs/index.md
    else
        echo "❌ No scenario logs found."
        echo "   Run tests with --log flag to generate logs."
        echo ""
        echo "Example:"
        echo "  just rm-test 5 --log"
    fi

# View specific scenario log
# Usage: just rm-log L1_01
rm-log LOG_ID:
    #!/usr/bin/env bash
    log_file="tmp/scenario_logs/{{ LOG_ID }}_*.md"
    # Use glob to find matching file
    found=$(ls $log_file 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        cat "$found"
    else
        echo "❌ Log file not found: {{ LOG_ID }}"
        echo ""
        echo "Available logs:"
        ls tmp/scenario_logs/L*.md 2>/dev/null || echo "  (none)"
    fi
