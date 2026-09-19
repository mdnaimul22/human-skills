#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "================================================================="
echo "🧪 Multi-OS Installation Verification Suite for human-skills"
echo "================================================================="
echo "Workspace: $WORKSPACE_ROOT"
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is required to run multi-OS verification tests." >&2
    exit 1
fi

DISTROS=(
    "amazonlinux:2023"
    "ubuntu:24.04"
    "debian:bookworm-slim"
    "alpine:latest"
    "fedora:latest"
)

TOTAL=${#DISTROS[@]}
PASSED=0
FAILED=0
RESULTS=()

for DISTRO in "${DISTROS[@]}"; do
    echo "-----------------------------------------------------------------"
    echo "🚀 Testing on: $DISTRO"
    echo "-----------------------------------------------------------------"
    START_TIME=$(date +%s)

    TEST_CMD="
set -e
if [ -f /etc/alpine-release ]; then
    SH_BIN=\"sh\"
else
    SH_BIN=\"bash\"
fi

cd /workspace
./scripts/install.sh

if ! command -v human-skills >/dev/null 2>&1; then
    export PATH=\"/usr/local/bin:\$HOME/.local/bin:\$PATH\"
fi

echo \"[Test 1] Executing: human-skills --list\"
LIST_OUTPUT=\$(human-skills --list)
if ! echo \"\$LIST_OUTPUT\" | grep -q \"Discovered Tools\"; then
    echo \"❌ Failed: human-skills --list did not return tool catalog\" >&2
    exit 1
fi

echo \"[Test 2] Executing: human-skills --list-all\"
LIST_ALL_OUTPUT=\$(human-skills --list-all)
if ! echo \"\$LIST_ALL_OUTPUT\" | grep -q \"ALL SKILLS\"; then
    echo \"❌ Failed: human-skills --list-all failed\" >&2
    exit 1
fi

echo \"[Test 3] Executing: human-skills --tool_info tree_gen\"
TOOL_OUTPUT=\$(human-skills --tool_info tree_gen)
if ! echo \"\$TOOL_OUTPUT\" | grep -q \"tree_gen\"; then
    echo \"❌ Failed: human-skills --tool_info tree_gen failed\" >&2
    exit 1
fi

echo \"✅ All checks passed on $DISTRO\"
"

    SHELL_PROG="sh"
    if [ "$DISTRO" != "alpine:latest" ]; then
        SHELL_PROG="bash"
    fi

    if docker run --rm \
        -v "$WORKSPACE_ROOT":/workspace \
        -w /workspace \
        "$DISTRO" \
        "$SHELL_PROG" -c "$TEST_CMD"; then
        
        END_TIME=$(date +%s)
        ELAPSED=$((END_TIME - START_TIME))
        RESULTS+=("PASS | $DISTRO | ${ELAPSED}s")
        PASSED=$((PASSED + 1))
        echo "✅ PASS: $DISTRO (${ELAPSED}s)"
    else
        END_TIME=$(date +%s)
        ELAPSED=$((END_TIME - START_TIME))
        RESULTS+=("FAIL | $DISTRO | ${ELAPSED}s")
        FAILED=$((FAILED + 1))
        echo "❌ FAIL: $DISTRO (${ELAPSED}s)"
    fi
    echo ""
done

echo "================================================================="
echo "📊 Multi-OS Verification Summary & Evidence Matrix"
echo "================================================================="
printf "%-8s | %-24s | %-10s\n" "STATUS" "OPERATING SYSTEM" "DURATION"
echo "-----------------------------------------------------------------"
for RES in "${RESULTS[@]}"; do
    STATUS=$(echo "$RES" | cut -d '|' -f 1 | xargs)
    OS_NAME=$(echo "$RES" | cut -d '|' -f 2 | xargs)
    DURATION=$(echo "$RES" | cut -d '|' -f 3 | xargs)
    if [ "$STATUS" = "PASS" ]; then
        printf "✅ %-6s | %-24s | %-10s\n" "$STATUS" "$OS_NAME" "$DURATION"
    else
        printf "❌ %-6s | %-24s | %-10s\n" "$STATUS" "$OS_NAME" "$DURATION"
    fi
done
echo "================================================================="
echo "Total Tests: $TOTAL | Passed: $PASSED | Failed: $FAILED"

if [ "$FAILED" -eq 0 ]; then
    echo "🎉 EMPIRICAL VERIFICATION COMPLETE: human-skills runs across ALL tested OSes!"
    exit 0
else
    echo "⚠️ Verification encountered failures."
    exit 1
fi
