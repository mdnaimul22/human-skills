#!/bin/bash

# Configuration
REPO_RAW_URL="https://raw.githubusercontent.com/mdnaimul22/human-skills/main"
RULES_DIR=".agent/rules"
RULES_FILES=("coding_standareds.md" "project_config_example.md" "project_tree_example.md")

echo "🚀 Starting Project Bootstrap..."

# 1. Create Directory Structure
echo "📁 Creating directories..."
DIRS=(
    "docs"
    "logs"
    "src/config"
    "src/core"
    "src/helpers"
    "src/providers"
    "src/schema"
    "src/services"
    "tests"
    "$RULES_DIR"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
    echo "   [Created] $dir"
done

# 2. Create __init__.py files
echo "📄 Initializing Python packages..."
INIT_FILES=(
    "src/__init__.py"
    "src/config/__init__.py"
    "src/core/__init__.py"
    "src/helpers/__init__.py"
    "src/providers/__init__.py"
    "src/schema/__init__.py"
    "src/services/__init__.py"
    "tests/__init__.py"
)

for file in "${INIT_FILES[@]}"; do
    touch "$file"
    echo "   [Created] $file"
done

# 3. Create basic files
echo "📄 Creating base files..."
touch .env
echo "# Environment Variables" > .env.example
echo "print('Hello from Project Skeleton!')" > main.py
echo "# New Project" > README.md
echo "   [Created] .env, .env.example, main.py, README.md"

# 4. Sync Agent Rules
echo "📥 Syncing Agent Rules from human-skills..."
for FILE in "${RULES_FILES[@]}"; do
    curl -sSL "$REPO_RAW_URL/.agent/rules/$FILE" -o "$RULES_DIR/$FILE"
    if [ $? -eq 0 ]; then
        echo "   [Synced] $FILE"
    else
        echo "   [Failed] $FILE"
    fi
done

echo -e "\n✨ Project Bootstrap Completed Successfully!"
echo "Happy Coding! 🎯"
