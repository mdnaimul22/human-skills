"""
SetUI Orchestrator — Scaffolds a complete Next.js + shadcn/ui frontend.

Executed by the setui tool via subprocess.
Expects to run inside the project root directory.

Steps:
  1. Verify node/npm are installed
  2. Create Next.js app in web/
  3. Install all dependencies (shadcn + extras) in one pass
  4. Setup shadcn config (pre-made components.json, skip `shadcn init`)
  5. Install Phase 1 shadcn components
  6. Copy custom template files from resources/
  7. Print success summary

Optimization: `shadcn init` is skipped entirely (~2.5 min saved).
Instead, components.json is pre-shipped and deps are merged into
a single `npm install` call after create-next-app.
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
WEB_DIR = PROJECT_DIR / "web"

SHADCN_COMPONENTS = [
    "button", "card", "input", "textarea", "select", "checkbox",
    "radio-group", "label", "badge", "table", "breadcrumb", "tabs",
    "pagination", "dialog", "alert-dialog", "tooltip", "alert",
    "skeleton", "spinner", "dropdown-menu", "sonner", "separator",
    "field", "form", "avatar", "scroll-area", "sheet", "popover",
    "switch", "sidebar",
]

# All deps in one list — shadcn runtime deps + project extras.
# Eliminates the separate `shadcn init` npm install (~2.5 min saved).
ALL_EXTRA_DEPS = [
    # shadcn/ui runtime deps (normally installed by `shadcn init`)
    "@base-ui/react", "class-variance-authority", "clsx",
    "lucide-react", "shadcn", "tailwind-merge", "tw-animate-css",
    # project extras
    "next-themes", "zustand",
]


# ── Helpers ────────────────────────────────────────────────────
def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command with output displayed."""
    return subprocess.run(
        cmd, cwd=str(cwd or PROJECT_DIR),
        capture_output=True, text=True, check=check
    )


SKIP_FILES = {"setup.py", "package.json", "package-lock.json", "tsconfig.json", "components.json"}
SKIP_DIRS  = {"node_modules", "__pycache__"}


def copy_tree(src: Path, dst: Path) -> list[str]:
    """Recursively copy src → dst, creating dirs as needed. Returns copied file list."""
    copied = []
    for item in src.rglob("*"):
        # Skip IDE-only and hidden files/dirs
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
        node_result = run(["node", "--version"], check=False)
        npm_result = run(["npm", "--version"], check=False)
        if node_result.returncode != 0 or npm_result.returncode != 0:
            print("❌ Node.js and npm are required. Install from: https://nodejs.org")
            sys.exit(1)
        print(f"   Node: {node_result.stdout.strip()}")
        print(f"   npm:  {npm_result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found. Install from: https://nodejs.org")
        sys.exit(1)


def step_create_nextjs():
    """Create Next.js app with TypeScript + Tailwind + App Router."""
    print("📦 Creating Next.js application...")
    if WEB_DIR.exists():
        print(f"   ⚠️ web/ already exists. Skipping create-next-app.")
        return

    result = run([
        "npx", "-y", "create-next-app@latest", "./web",
        "--typescript",
        "--tailwind",
        "--eslint",
        "--app",
        "--src-dir",
        "--import-alias", "@/*",
        "--use-npm",
    ])
    if result.returncode != 0:
        print(f"❌ create-next-app failed:\n{result.stderr}")
        sys.exit(1)
    print("   ✅ Next.js app created")


def step_install_deps():
    """Install all extra deps in a single npm install pass.

    Merges shadcn runtime deps + project extras to avoid the
    separate `shadcn init` step (~2.5 min saved).
    """
    print(f"📥 Installing {len(ALL_EXTRA_DEPS)} dependencies...")
    result = run(
        ["npm", "install", *ALL_EXTRA_DEPS],
        cwd=WEB_DIR, check=False
    )
    if result.returncode == 0:
        print(f"   ✅ All dependencies installed")
    else:
        print(f"   ⚠️ npm install warning: {result.stderr[:200]}")


def step_setup_shadcn_config():
    """Copy pre-made components.json instead of running `shadcn init`.

    This skips the ~2.5 min `shadcn init` process which mostly
    just runs `npm install` (already done) and creates this file.
    """
    print("🎨 Setting up shadcn/ui config...")
    src = RESOURCES_DIR / "components.json"
    dst = WEB_DIR / "components.json"
    if src.exists():
        shutil.copy2(src, dst)
        print("   ✅ components.json installed (shadcn init skipped)")
    else:
        print("   ⚠️ components.json not found in resources, running shadcn init...")
        run(["npx", "-y", "shadcn@latest", "init", "-d", "-y"], cwd=WEB_DIR, check=False)
        print("   ✅ shadcn/ui initialized (fallback)")


def step_add_components():
    """Install Phase 1 shadcn components."""
    print(f"🧩 Installing {len(SHADCN_COMPONENTS)} shadcn components...")
    result = run(
        ["npx", "shadcn@latest", "add", *SHADCN_COMPONENTS, "-y", "--overwrite"],
        cwd=WEB_DIR, check=False
    )
    if result.returncode != 0:
        print(f"   ⚠️ Some components may have failed. Continuing...")
        print(f"   stderr: {result.stderr[:200]}")
    else:
        print(f"   ✅ {len(SHADCN_COMPONENTS)} components installed")


def step_copy_templates():
    """Copy custom template files from resources/ui/ into web/src/."""
    print("📄 Copying custom templates...")
    web_src = WEB_DIR / "src"

    copied = []

    # globals.css → overwrite the one create-next-app generated
    src_css = RESOURCES_DIR / "globals.css"
    if src_css.exists():
        dst_css = web_src / "app" / "globals.css"
        shutil.copy2(src_css, dst_css)
        copied.append("app/globals.css")

    # app/ templates (layout, pages)
    app_src = RESOURCES_DIR / "app"
    if app_src.exists():
        copied.extend(copy_tree(app_src, web_src / "app"))

    # components/ templates
    comp_src = RESOURCES_DIR / "components"
    if comp_src.exists():
        copied.extend(copy_tree(comp_src, web_src / "components"))

    # lib/ templates
    lib_src = RESOURCES_DIR / "lib"
    if lib_src.exists():
        copied.extend(copy_tree(lib_src, web_src / "lib"))

    # hooks/ templates
    hooks_src = RESOURCES_DIR / "hooks"
    if hooks_src.exists():
        copied.extend(copy_tree(hooks_src, web_src / "hooks"))

    # scripts/ (generate-types.sh)
    scripts_src = RESOURCES_DIR / "scripts"
    if scripts_src.exists():
        scripts_dst = WEB_DIR / "scripts"
        copied.extend(copy_tree(scripts_src, scripts_dst))

    # Create types/ placeholder
    types_dir = web_src / "types"
    types_dir.mkdir(parents=True, exist_ok=True)
    api_types = types_dir / "api.ts"
    if not api_types.exists():
        api_types.write_text(
            '// Auto-generated TypeScript types from FastAPI OpenAPI spec.\n'
            '// Run: bash scripts/generate-types.sh\n'
            '// DO NOT EDIT MANUALLY.\n\n'
            'export {};\n'
        )
        copied.append("types/api.ts")

    for f in sorted(copied):
        print(f"   [Created] {f}")


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

    # ── Determine color-scheme (light/dark) from background luminance ──
    bg_hex = colors.get("background", "#f8fafc").lstrip("#")
    if len(bg_hex) == 6:
        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    else:
        luminance = 0.9  # default to light
    is_light = luminance > 0.5
    scheme = "light" if is_light else "dark"

    # ── Build CSS block ──
    primary = colors.get("primary", "#3b82f6")
    secondary = colors.get("secondary", "#6366f1")
    accent = colors.get("accent", colors.get("cta", "#f97316"))
    bg = colors.get("background", "#f8fafc")
    fg = colors.get("foreground", colors.get("text", "#1e293b"))
    muted = colors.get("muted", "#f1f5f9" if is_light else "#334155")
    border = colors.get("border", "#e2e8f0" if is_light else "#334155")
    destructive = colors.get("destructive", "#ef4444")
    ring = colors.get("ring", primary)

    # Derive sub-tokens
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

    # ── Inject into globals.css ──
    globals_path = WEB_DIR / "src" / "app" / "globals.css"
    if globals_path.exists():
        content = globals_path.read_text(encoding="utf-8")
        # Insert before BRIDGE MAPPING section
        marker = "/* ═══════════════════════════════════════════════════════════════\n   BRIDGE MAPPING"
        if marker in content:
            content = content.replace(marker, css_block + marker)
        else:
            # Fallback: append before shadcn mapping
            content += css_block

        # Add "custom" to bridge mapping selector so it gets shadcn vars
        bridge_old = '[data-theme="jam-navy"] {'
        bridge_new = '[data-theme="custom"],\n[data-theme="jam-navy"] {'
        if bridge_old in content and '[data-theme="custom"]' not in content.split("BRIDGE MAPPING")[1] if "BRIDGE MAPPING" in content else True:
            content = content.replace(bridge_old, bridge_new, 1)

        globals_path.write_text(content, encoding="utf-8")
        print("   [Injected] globals.css — custom theme")

    # ── Inject Google Fonts into layout.tsx ──
    heading_font = typography.get("heading", "Inter")
    body_font = typography.get("body", "Inter")
    google_url = typography.get("google_fonts_url", "")

    layout_path = WEB_DIR / "src" / "app" / "layout.tsx"
    if layout_path.exists() and google_url:
        layout_content = layout_path.read_text(encoding="utf-8")

        # Add Google Fonts <link> before </head> or in <head> section
        font_link = f'        <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
        font_link += f'        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />\n'
        font_link += f'        <link href="{google_url}" rel="stylesheet" />\n'

        # Insert after <head> or before </head>
        if "<head>" in layout_content and font_link.strip() not in layout_content:
            layout_content = layout_content.replace("<head>", f"<head>\n{font_link}", 1)

        layout_path.write_text(layout_content, encoding="utf-8")
        print(f"   [Injected] layout.tsx — Google Fonts ({heading_font} / {body_font})")

    # ── Update font-sans in globals.css ──
    if globals_path.exists():
        content = globals_path.read_text(encoding="utf-8")
        old_font = "--font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;"
        new_font = f"--font-sans: '{heading_font}', '{body_font}', ui-sans-serif, system-ui, sans-serif;"
        if old_font in content:
            content = content.replace(old_font, new_font)
            globals_path.write_text(content, encoding="utf-8")
            print(f"   [Patched] --font-sans → {heading_font} / {body_font}")

    # ── Set default theme to "custom" in theme provider ──
    theme_path = WEB_DIR / "src" / "components" / "layout" / "theme.tsx"
    if theme_path.exists():
        theme_content = theme_path.read_text(encoding="utf-8")
        # Replace defaultTheme if found
        if 'defaultTheme="dark"' in theme_content:
            theme_content = theme_content.replace('defaultTheme="dark"', 'defaultTheme="custom"')
            theme_path.write_text(theme_content, encoding="utf-8")
            print("   [Patched] default theme → custom")

    print(f"   ✅ Design system injected ({project_name})")


# ── Color utility helpers (pure string, no external deps) ────────
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
    """Print success summary."""
    ds_json = os.environ.get("DESIGN_SYSTEM_JSON", "")
    has_custom = bool(ds_json)

    print("\n" + "═" * 55)
    print("✨ SetUI Completed Successfully!")
    print("═" * 55)
    print()
    print("📋 Next steps:")
    print("   1. cd web && npm run dev")
    print("   2. Open http://localhost:3000")
    print("   3. Add NEXT_PUBLIC_API_URL to web/.env.local")
    print("   4. Generate types: bash web/scripts/generate-types.sh")
    print()
    if has_custom:
        try:
            ds = json.loads(ds_json)
            name = ds.get("project_name", "Custom")
            style = ds.get("style", {}).get("name", "")
            print(f"🧠 AI Design System: {name}")
            if style:
                print(f"   Style: {style}")
            print(f"   Default theme: custom (AI-generated)")
        except json.JSONDecodeError:
            pass
    else:
        print("🎨 Themes available: dark, matrix, cream, matte-black,")
        print("   black-brown, jam-black, jam-navy, light, snow")
    print()
    print("Happy Coding! 🎯")


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting SetUI...\n")

    step_check_node()
    step_create_nextjs()
    step_install_deps()          # single npm install — all deps at once
    step_setup_shadcn_config()   # pre-made components.json (skips shadcn init)
    step_add_components()
    step_copy_templates()
    step_inject_design_system()
    step_summary()
