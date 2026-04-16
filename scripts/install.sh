#!/bin/bash

echo "🚀 Installing human-skills global command..."

# Get the absolute path of the human-skills project directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXEC_PATH="$REPO_DIR/skills/helpers/execute.py"

# Verify the execute script exists
if [ ! -f "$EXEC_PATH" ]; then
    echo "❌ Error: Could not find execute.py at $EXEC_PATH"
    echo "Make sure you are running this script from within the human-skills repository."
    exit 1
fi

# Ensure ~/.local/bin exists
DEST_DIR="$HOME/.local/bin"
mkdir -p "$DEST_DIR"

DEST_FILE="$DEST_DIR/human-skills"

# Create the bash wrapper
cat << EOF > "$DEST_FILE"
#!/bin/bash
python3 "$EXEC_PATH" "\$@"
EOF

# Make it executable
chmod +x "$DEST_FILE"

echo "✅ 'human-skills' installed successfully to $DEST_FILE!"
echo ""
echo "You can now use the Universal Command from ANY directory:"
echo "  🔹 human-skills --list"
echo "  🔹 human-skills --skill_info directory-structure"
echo "  🔹 human-skills --tool_info tree_gen"
echo ""
echo "💡 Note: If you get a 'command not found' error, you may need to add ~/.local/bin to your system PATH or simply restart your terminal."
