#!/bin/bash

# Target directory
TARGET_DIR=".agents/rules"
REPO_RAW_URL="https://raw.githubusercontent.com/mdnaimul22/human-skills/main/.agents/rules"

# Files to sync
FILES=("coding_standareds.md" "project_config_example.md" "project_tree_example.md")

echo "--- Rules Sync Started ---"

# Create directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating directory $TARGET_DIR..."
    mkdir -p "$TARGET_DIR"
fi

# Download/Update files
for FILE in "${FILES[@]}"; do
    echo "Syncing $FILE..."
    curl -sSL "$REPO_RAW_URL/$FILE" -o "$TARGET_DIR/$FILE"
    if [ $? -eq 0 ]; then
        echo "Successfully synced $FILE"
    else
        echo "Failed to sync $FILE"
    fi
done

echo "--- Rules Sync Completed ---"
