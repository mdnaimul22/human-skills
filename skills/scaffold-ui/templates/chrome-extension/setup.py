"""
SetUI Chrome Extension Orchestrator — Scaffolds a React + Vite Chrome Extension.

Executed by the setui tool via subprocess.
Expects to run inside the project root directory.

Steps:
  1. Verify node/npm are installed
  2. Copy template structure to extension/
  3. Inject AI custom design system if provided
  4. Print summary
"""

import json
import os
import subprocess
import shutil
import sys
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────
RESOURCES_DIR = Path(__file__).resolve().parent
PROJECT_DIR = Path.cwd()
EXTENSION_DIR = PROJECT_DIR / "extension"

SKIP_FILES = {"setup.py"}
SKIP_DIRS  = {"node_modules", "__pycache__"}

def copy_tree(src: Path, dst: Path) -> list[str]:
    """Recursively copy src → dst, creating dirs as needed. Returns copied file list."""
    copied = []
    for item in src.rglob("*"):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if item.is_file() and not item.name.startswith(".") and item.name not in SKIP_FILES:
            rel = item.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied.append(str(rel))
    return copied

# ── Step Functions ─────────────────────────────────────────────
def step_check_node():
    """Verify node and npm are available."""
    print("🔍 Checking Node.js and npm...")
    try:
        node_result = subprocess.run(["node", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        npm_result = subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if node_result.returncode != 0 or npm_result.returncode != 0:
            print("❌ Node.js and npm are required. Install from: https://nodejs.org")
            sys.exit(1)
        print(f"   Node: {node_result.stdout.strip()}")
        print(f"   npm:  {npm_result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found. Install from: https://nodejs.org")
        sys.exit(1)

def step_create_structure():
    """Copy pre-shipped structure directly."""
    print("📂 Creating extension directory structure...")
    if EXTENSION_DIR.exists():
        print("   ⚠️ Destination 'extension/' folder already exists. Files may be overwritten.")
    
    EXTENSION_DIR.mkdir(parents=True, exist_ok=True)
    
    copied = copy_tree(RESOURCES_DIR, EXTENSION_DIR)
    for f in sorted(copied):
        print(f"   [Created] {f}")
    print("   ✅ Directory structure ready")

def step_inject_design_system():
    """Inject AI-generated custom theme from ui-ux-pro-max design system."""
    ds_json = os.environ.get("DESIGN_SYSTEM_JSON", "")
    if not ds_json:
        return

    print("🧠 Injecting AI-generated design system...")

    try:
        ds = json.loads(ds_json)
    except json.JSONDecodeError:
        print("   ⚠️ Invalid design system JSON. Skipping.")
        return

    colors = ds.get("colors", {})
    typography = ds.get("typography", {})
    project_name = ds.get("project_name", "Custom")

    # Determine light/dark color scheme
    bg_hex = colors.get("background", "#f8fafc").lstrip("#")
    if len(bg_hex) == 6:
        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    else:
        luminance = 0.9
    is_light = luminance > 0.5
    scheme = "light" if is_light else "dark"

    # Compile CSS tokens
    primary = colors.get("primary", "#3b82f6")
    secondary = colors.get("secondary", "#6366f1")
    accent = colors.get("accent", colors.get("cta", "#f97316"))
    bg = colors.get("background", "#f8fafc")
    fg = colors.get("foreground", colors.get("text", "#1e293b"))
    muted = colors.get("muted", "#f1f5f9" if is_light else "#334155")
    border = colors.get("border", "#e2e8f0" if is_light else "#334155")
    destructive = colors.get("destructive", "#ef4444")
    ring = colors.get("ring", primary)

    surface = "#ffffff" if is_light else _lighten_hex(bg, 0.08)
    primary_fg = "#ffffff"
    text_secondary = _blend_hex(fg, bg, 0.3)
    text_muted = _blend_hex(fg, bg, 0.5)

    css_block = f"""

/* ═══════════════════════════════════════════════════════════════
   THEME 10: CUSTOM — AI-Generated ({project_name})
   Source: ui-ux-pro-max design system
   ═══════════════════════════════════════════════════════════════ */
[data-theme="custom"] {{
    color-scheme: {scheme};

    --color-primary: {primary};
    --color-primary-dark: {_darken_hex(primary, 0.15)};
    --color-primary-light: {_alpha_hex(primary, 0.12)};
    --color-primary-foreground: {primary_fg};

    --color-success: #16a34a;
    --color-warning: #ca8a04;
    --color-danger: {destructive};

    --color-bg: {bg};
    --color-surface: {surface};
    --color-card: {surface};
    --color-input: {muted};

    --color-text: {fg};
    --color-text-secondary: {text_secondary};
    --color-text-muted: {text_muted};
    --color-text-inverse: {bg};

    --color-border: {border};
    --color-border-hover: {_darken_hex(border, 0.1)};
    --color-border-subtle: {muted};

    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, {"0.05" if is_light else "0.3"});
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, {"0.1" if is_light else "0.4"});
    --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, {"0.1" if is_light else "0.5"});
    --ring-color: {_alpha_hex(ring, 0.35)};
}}
"""

    globals_path = EXTENSION_DIR / "src" / "styles" / "globals.css"
    if globals_path.exists():
        content = globals_path.read_text(encoding="utf-8")
        marker = "/* ═══════════════════════════════════════════════════════════════\n   BRIDGE MAPPING"
        if marker in content:
            content = content.replace(marker, css_block + marker)
        else:
            content += css_block

        # Inject selector for custom theme in bridge mapping
        bridge_old = '[data-theme="jam-navy"] {'
        bridge_new = '[data-theme="custom"],\n[data-theme="jam-navy"] {'
        if bridge_old in content:
            content = content.replace(bridge_old, bridge_new, 1)

        # Update font-sans
        heading_font = typography.get("heading", "Inter")
        body_font = typography.get("body", "Inter")
        old_font = "--font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;"
        new_font = f"--font-sans: '{heading_font}', '{body_font}', ui-sans-serif, system-ui, sans-serif;"
        if old_font in content:
            content = content.replace(old_font, new_font)

        globals_path.write_text(content, encoding="utf-8")
        print("   [Injected] globals.css — custom theme")

    # Set default theme to "custom" in theme provider
    theme_path = EXTENSION_DIR / "src" / "components" / "layout" / "theme-provider.tsx"
    if theme_path.exists():
        theme_content = theme_path.read_text(encoding="utf-8")
        if "defaultTheme = 'dark'" in theme_content:
            theme_content = theme_content.replace("defaultTheme = 'dark'", "defaultTheme = 'custom'")
            theme_path.write_text(theme_content, encoding="utf-8")
            print("   [Patched] default theme → custom")

    print(f"   ✅ Design system injected ({project_name})")

# Color helpers
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"

def _darken_hex(h: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(h)
    return _rgb_to_hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))

def _lighten_hex(h: str, amount: float) -> str:
    r, g, b = _hex_to_rgb(h)
    return _rgb_to_hex(int(r + (255 - r) * amount), int(g + (255 - g) * amount), int(b + (255 - b) * amount))

def _alpha_hex(h: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(h)
    return f"rgba({r}, {g}, {b}, {alpha})"

def _blend_hex(fg: str, bg: str, ratio: float) -> str:
    r1, g1, b1 = _hex_to_rgb(fg)
    r2, g2, b2 = _hex_to_rgb(bg)
    return _rgb_to_hex(
        int(r1 * (1 - ratio) + r2 * ratio),
        int(g1 * (1 - ratio) + g2 * ratio),
        int(b1 * (1 - ratio) + b2 * ratio),
    )

def step_summary():
    """Print summary."""
    ds_json = os.environ.get("DESIGN_SYSTEM_JSON", "")
    has_custom = bool(ds_json)

    print("\n" + "═" * 55)
    print("✨ Chrome Extension Scaffold Completed Successfully!")
    print("═" * 55)
    print()
    print("📋 Next steps to run:")
    print("   1. cd extension")
    print("   2. npm install")
    print("   3. npm run build")
    print("   4. Open Google Chrome, go to chrome://extensions/")
    print("   5. Turn on 'Developer Mode' (top right)")
    print("   6. Click 'Load unpacked' and select the 'extension/dist' folder")
    print()
    if has_custom:
        try:
            ds = json.loads(ds_json)
            name = ds.get("project_name", "Custom")
            print(f"🧠 AI Design System: {name}")
            print(f"   Default theme: custom (AI-generated)")
        except json.JSONDecodeError:
            pass
    print()
    print("Happy Coding! 🎯")

if __name__ == "__main__":
    print("🚀 Starting Chrome Extension Scaffold...\n", flush=True)

    STEPS = [
        ("check-node",          step_check_node),
        ("create-structure",    step_create_structure),
        ("inject-design",       step_inject_design_system),
        ("summary",             step_summary),
    ]

    for step_name, step_fn in STEPS:
        try:
            step_fn()
        except subprocess.TimeoutExpired:
            print(f"\n❌ TIMEOUT during step: {step_name}", flush=True)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"\n❌ FAILED at step: {step_name} (exit code {e.returncode})", flush=True)
            if e.stdout:
                print(f"   Output: {e.stdout[-300:]}", flush=True)
            sys.exit(1)
        except SystemExit:
            raise
        except Exception as e:
            print(f"\n❌ ERROR at step: {step_name}: {e}", flush=True)
            sys.exit(1)
