#!/bin/bash

# Configuration
REPO_RAW_URL="https://raw.githubusercontent.com/mdnaimul22/human-skills/main"
RULES_DIR=".agent/rules"
RULES_FILES=("coding_standareds.md" "project_config_example.md" "project_tree_example.md")

echo "🚀 Starting Project Bootstrap..."

# Safety Check: Ensure the directory is empty
if [ "$(ls -A)" ]; then
    echo -e "⚠️  Error: This directory is not empty!"
    echo "❌ দুঃখিত, এই মডিউল শুধুমাত্র নতুন প্রজেক্ট ইনিশিয়েলাইজ করার জন্য। পুরাতন প্রজেক্টে এটি রান করলে প্রজেক্ট ধ্বংস হয়ে যেতে পারে।"
    exit 1
fi

# 1. Create Directory Structure
echo "📁 Creating directories..."
DIRS=(
    "docs"
    "logs"
    "src/configs"
    "src/core"
    "src/helpers"
    "src/providers"
    "src/schema"
    "src/services"
    "src/routers"
    "tests"
    "$RULES_DIR"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
    echo "   [Created] $dir"
done

# 2. Create __init__.py files with conventions
echo "📄 Initializing Python packages with conventions..."

function create_init() {
    local file=$1
    local msg=$2
    echo -e "\"\"\"\n$msg\n\"\"\"" > "$file"
    echo "   [Created] $file"
}

create_init "src/__init__.py" "Global source package."
create_init "src/configs/__init__.py" "Config is isolated. All environment settings must be aggregated here and exposed via a Single Source of Truth."
create_init "src/core/__init__.py" "Core business logic. Domain models and pure functional flows live here."
create_init "src/helpers/__init__.py" "Global utilities and stateless helpers used across the entire project."
create_init "src/providers/__init__.py" "External service integrations (LLM, Database, API clients) only."
create_init "src/schema/__init__.py" "Single source of truth for Pydantic models and data structures. No business logic allowed."
create_init "src/services/__init__.py" "Fan-in point. Orchestrates Core logic and Providers. This is the only layer where Core and Providers converge to fulfill application-specific use cases. Business logic stays in Core, while Services handle the high-level orchestration."
create_init "src/routers/__init__.py" "Acts as the HTTP interface for the application services. No business logic allowed."
create_init "tests/__init__.py" "Test suite for the project."

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
