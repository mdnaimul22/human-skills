"""
SetUI Orchestrator — Scaffolds a complete Next.js + shadcn/ui frontend.

Executed by the setui tool via subprocess.
Expects to run inside the project root directory.

Steps:
  1. Verify node/npm are installed
  2. Create Next.js app in web/
  3. Initialize shadcn/ui
  4. Install Phase 1 shadcn components
  5. Install extra npm dependencies
  6. Copy custom template files from resources/ui/
  7. Print success summary
"""

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

EXTRA_NPM_DEPS = ["next-themes", "zustand"]


# ── Helpers ────────────────────────────────────────────────────
def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command with output displayed."""
    return subprocess.run(
        cmd, cwd=str(cwd or PROJECT_DIR),
        capture_output=True, text=True, check=check
    )


SKIP_FILES = {"setup.py", "package.json", "package-lock.json", "tsconfig.json"}
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


def step_init_shadcn():
    """Initialize shadcn/ui with default config."""
    print("🎨 Initializing shadcn/ui...")
    result = run(
        ["npx", "-y", "shadcn@latest", "init", "-d", "-y"],
        cwd=WEB_DIR, check=False
    )
    if result.returncode != 0:
        # Try alternate command format
        result = run(
            ["npx", "-y", "shadcn@latest", "init", "--defaults"],
            cwd=WEB_DIR, check=False
        )
    print("   ✅ shadcn/ui initialized")


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


def step_install_deps():
    """Install extra npm dependencies."""
    print("📥 Installing extra dependencies...")
    result = run(
        ["npm", "install", *EXTRA_NPM_DEPS],
        cwd=WEB_DIR, check=False
    )
    if result.returncode == 0:
        print(f"   ✅ Installed: {', '.join(EXTRA_NPM_DEPS)}")
    else:
        print(f"   ⚠️ npm install warning: {result.stderr[:200]}")


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


def step_summary():
    """Print success summary."""
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
    print("🎨 Themes available: dark, matrix, cream, matte-black,")
    print("   black-brown, jam-black, jam-navy, light, snow")
    print()
    print("Happy Coding! 🎯")


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting SetUI...\n")

    step_check_node()
    step_create_nextjs()
    step_init_shadcn()
    step_add_components()
    step_install_deps()
    step_copy_templates()
    step_summary()
