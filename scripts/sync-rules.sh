#!/bin/bash

# Target directory
TARGET_DIR=".agents/rules"
API_URL="https://api.github.com/repos/mdnaimul22/human-skills/contents/.agents/rules"
REPO_RAW_URL="https://raw.githubusercontent.com/mdnaimul22/human-skills/main/.agents/rules"

echo "--- Rules Sync Started ---"

# Create directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating directory $TARGET_DIR..."
    mkdir -p "$TARGET_DIR"
fi

# Fetch list of files dynamically from GitHub API
echo "Fetching latest rules list from repository..."
DYNAMIC_FILES=$(curl -sSL "$API_URL" | python3 -c "import json, sys; [print(x['name']) for x in json.load(sys.stdin) if isinstance(x, dict) and x.get('type') == 'file' and x.get('name', '').endswith('.md')]" 2>/dev/null)

if [ -n "$DYNAMIC_FILES" ]; then
    readarray -t FILES <<< "$DYNAMIC_FILES"
else
    # Fallback list if GitHub API is unreachable or rate limited
    FILES=(
        "coding-standards.md"
        "architecture-patterns.md"
        "maintenance-testing.md"
        "config-path-rules.md"
        "config-usage-rules.md"
        "helpers-usage-rules.md"
        "project-config-example.md"
        "project-tree-example.md"
        "common-git-workflow.md"
    )
fi

# Download/Update files
for FILE in "${FILES[@]}"; do
    [ -z "$FILE" ] && continue
    echo "Syncing $FILE..."
    curl -sSL "$REPO_RAW_URL/$FILE" -o "$TARGET_DIR/$FILE"
    if [ $? -eq 0 ]; then
        echo "Successfully synced $FILE"
    else
        echo "Failed to sync $FILE"
    fi
done

echo "--- Rules Sync Completed ---"
