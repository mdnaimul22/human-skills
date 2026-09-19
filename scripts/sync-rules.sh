#!/usr/bin/env sh
set -e

REPO_URL="https://github.com/mdnaimul22/human-skills.git"
TAR_URL="https://github.com/mdnaimul22/human-skills/archive/refs/heads/main.tar.gz"
TARGET_DIR="${1:-.agents}"

echo "🚀 Syncing .agents directory into $TARGET_DIR..."

TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'agents_sync')"
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

SYNC_SUCCESS=0

if command -v git >/dev/null 2>&1; then
    if git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" "$TMP_DIR/repo" >/dev/null 2>&1; then
        (cd "$TMP_DIR/repo" && git sparse-checkout set .agents >/dev/null 2>&1)
        if [ -d "$TMP_DIR/repo/.agents" ]; then
            mkdir -p "$TARGET_DIR"
            cp -R "$TMP_DIR/repo/.agents/." "$TARGET_DIR/"
            SYNC_SUCCESS=1
        fi
    fi
fi

if [ "$SYNC_SUCCESS" -ne 1 ]; then
    if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
        if curl -sSL "$TAR_URL" | tar -xz -C "$TMP_DIR" >/dev/null 2>&1; then
            SOURCE_AGENTS="$(find "$TMP_DIR" -type d -name ".agents" | head -n 1)"
            if [ -n "$SOURCE_AGENTS" ] && [ -d "$SOURCE_AGENTS" ]; then
                mkdir -p "$TARGET_DIR"
                cp -R "$SOURCE_AGENTS/." "$TARGET_DIR/"
                SYNC_SUCCESS=1
            fi
        fi
    fi
fi

if [ "$SYNC_SUCCESS" -ne 1 ]; then
    echo "❌ Error: Failed to sync .agents directory from $REPO_URL" >&2
    exit 1
fi

echo "================================================================="
echo "✅ Rules synchronization completed successfully!"
echo "📁 Target directory: $TARGET_DIR"
if [ -d "$TARGET_DIR/rules" ]; then
    echo "📋 Synced rule files:"
    for rule_file in "$TARGET_DIR/rules/"*.md; do
        if [ -f "$rule_file" ]; then
            echo "   • $(basename "$rule_file")"
        fi
    done
fi
echo "================================================================="
