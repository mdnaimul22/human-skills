#!/usr/bin/env sh
set -e

echo "🚀 Installing human-skills global CLI dispatcher..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXEC_PATH="$REPO_DIR/skills/helpers/execute.py"

if [ ! -f "$EXEC_PATH" ]; then
    echo "❌ Error: Could not find execute.py at $EXEC_PATH" >&2
    echo "Make sure you are running this script from within the human-skills repository." >&2
    exit 1
fi

PYTHON_BIN=""
for candidate in python3 python python3.13 python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v "$candidate")"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️ Python 3 (>= 3.8) not detected on this system."
    if [ "$(id -u)" -eq 0 ]; then
        echo "📦 Attempting to install Python 3 via package manager..."
        if command -v dnf >/dev/null 2>&1; then
            dnf install -y python3
        elif command -v yum >/dev/null 2>&1; then
            yum install -y python3
        elif command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y -qq python3
        elif command -v apk >/dev/null 2>&1; then
            apk add --no-cache python3
        elif command -v pacman >/dev/null 2>&1; then
            pacman -Sy --noconfirm python
        elif command -v zypper >/dev/null 2>&1; then
            zypper install -y python3
        fi
    elif command -v sudo >/dev/null 2>&1; then
        echo "📦 Attempting to install Python 3 with sudo..."
        if command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y python3
        elif command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -qq && sudo apt-get install -y -qq python3
        elif command -v apk >/dev/null 2>&1; then
            sudo apk add --no-cache python3
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -Sy --noconfirm python
        elif command -v brew >/dev/null 2>&1; then
            brew install python3
        fi
    fi

    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
                PYTHON_BIN="$(command -v "$candidate")"
                break
            fi
        fi
    done

    if [ -z "$PYTHON_BIN" ]; then
        echo "❌ Error: Python 3 (>= 3.8) is required but could not be installed automatically." >&2
        echo "Please install Python 3 using your system package manager and re-run." >&2
        exit 1
    fi
fi

PYTHON_VER="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "🐍 Detected Python: $PYTHON_BIN (v$PYTHON_VER)"

if [ "$(id -u)" -eq 0 ] || [ -w "/usr/local/bin" ]; then
    DEST_DIR="/usr/local/bin"
else
    DEST_DIR="$HOME/.local/bin"
fi

mkdir -p "$DEST_DIR"
DEST_FILE="$DEST_DIR/human-skills"

cat << EOF > "$DEST_FILE"
#!/usr/bin/env sh
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$EXEC_PATH" "\$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$EXEC_PATH" "\$@"
else
    echo "❌ Error: Python 3 not found in PATH." >&2
    exit 127
fi
EOF

chmod +x "$DEST_FILE"

PATH_CONFIGURED=1
case ":$PATH:" in
    *":$DEST_DIR:"*) ;;
    *)
        PATH_CONFIGURED=0
        PATH_EXPORT="export PATH=\"$DEST_DIR:\$PATH\""
        for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
            if [ -f "$rc_file" ] || [ "$(basename "${SHELL:-sh}")" = "$(basename "${rc_file#.}" | sed 's/rc//')" ]; then
                if ! grep -q "$DEST_DIR" "$rc_file" 2>/dev/null; then
                    printf "\n# Added by human-skills installer\n%s\n" "$PATH_EXPORT" >> "$rc_file" 2>/dev/null || true
                    PATH_CONFIGURED=1
                fi
            fi
        done
        export PATH="$DEST_DIR:$PATH"
        ;;
esac

echo "🔍 Verifying installation..."
if "$DEST_FILE" --list >/dev/null 2>&1; then
    echo "✅ Verification passed! 'human-skills' command is verified functional."
else
    echo "❌ Verification failed: '$DEST_FILE' could not be executed." >&2
    exit 1
fi

echo ""
echo "================================================================="
echo "🎉 human-skills installed successfully!"
echo "📍 Binary Location: $DEST_FILE"
if [ "$PATH_CONFIGURED" -eq 1 ] && [ "$DEST_DIR" != "/usr/local/bin" ]; then
    echo "🔄 Shell Profile Updated: Added $DEST_DIR to your shell rc files."
fi
echo ""
echo "You can now run 'human-skills' from ANY directory:"
echo "  • human-skills --list"
echo "  • human-skills --skill_info architecture-auditing-linter"
echo "  • human-skills --tool_info linter"
echo "================================================================="
