from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from helpers.tool import Tool, Response

class SetUI(Tool):
    name: str = "setui"
    description: str = (
        "Scaffolds a complete Next.js frontend (web/) or React Chrome Extension (extension/) "
        "with 11 themes, layout components, secure API client, and layout pages. "
        "Optionally accepts a 'design_query' to generate an AI-powered custom theme via ui-ux-pro-max."
    )
    arguments: dict = {
        "destination": "Project root where the client directory should be created (e.g. '/path/to/project').",
        "action": "(Optional) The client template to scaffold: 'frontend' (default, Next.js web client) or 'chrome-extension' (React extension).",
        "design_query": "(Optional) Product/industry description for AI design system generation. "
                        "Example: 'beauty spa wellness', 'fintech crypto dashboard', 'SaaS analytics'. "
                        "When provided, generates a custom theme with industry-matched colors and fonts.",
        "density": "(Optional) Visual density dial (1-10): 1-3=spacious layout, 4-7=standard, 8-10=compact dashboard.",
        "motion": "(Optional) Motion intensity dial (1-10): 1-3=subtle micro-interactions, 4-7=standard, 8-10=complex choreography.",
    }
    instruction: str = (
        "Use this tool to set up a modern frontend layer for any Python/FastAPI project. "
        "Requires Node.js and npm to be installed. "
        "Pass 'design_query' to auto-generate a custom theme matched to your industry/product."
    )

    def _persist_brand_and_tokens(self, ds: dict, base_dir: Path) -> None:
        project_name = ds.get("project_name") or "default"
        slug = re.sub(r"[^a-z0-9_-]+", "-", project_name.lower()).strip("-") or "default"
        colors = ds.get("colors", {})
        typography = ds.get("typography", {})
        spacing = ds.get("spacing_scale", {})

        docs_dir = base_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        brand_path = docs_dir / "brand-guidelines.md"

        category = ds.get("category", "General")
        primary = colors.get("primary", "#3B82F6")
        secondary = colors.get("secondary", "#6366F1")
        accent = colors.get("accent", "#F97316")
        bg = colors.get("background", "#F8FAFC")
        fg = colors.get("foreground", "#1E293B")
        card = colors.get("card", "#FFFFFF")
        muted = colors.get("muted", "#F1F5F9")
        border = colors.get("border", "#E2E8F0")
        on_primary = colors.get("on_primary", "#FFFFFF")
        heading = typography.get("heading", "Inter")
        body = typography.get("body", "Inter")
        google_url = typography.get("google_fonts_url", "")
        anti_patterns = ds.get("anti_patterns", "")

        brand_content = f"""# Brand Guidelines v1.0 — {project_name}

> Category: {category}
> Generated via ui-ux-pro-max design intelligence
> Status: Active

## Quick Reference

| Element | Value | Usage |
|---|---|---|
| Primary Color | `{primary}` | Brand identification, primary CTAs |
| Primary FG | `{on_primary}` | Accessible text on primary button |
| Secondary Color | `{secondary}` | Supporting accents |
| Background | `{bg}` | Canvas base |
| Surface / Card | `{card}` | Elevated panels |
| Heading Font | `{heading}` | Titles, headers |
| Body Font | `{body}` | Reading copy, UI text |

---

## 1. Color Palette

### Primary & Accent Colors

| Role | Hex | Token |
|---|---|---|
| Primary | `{primary}` | `--color-primary` |
| Primary Foreground | `{on_primary}` | `--color-primary-foreground` |
| Secondary | `{secondary}` | `--color-secondary` |
| Accent / CTA | `{accent}` | `--color-accent` |

### Neutral Palette

| Role | Hex | Token |
|---|---|---|
| Background | `{bg}` | `--color-bg` |
| Surface / Card | `{card}` | `--color-card` |
| Input / Muted | `{muted}` | `--color-input` |
| Border | `{border}` | `--color-border` |
| Text Primary | `{fg}` | `--color-text` |

---

## 2. Typography

- **Heading Font**: {heading}
- **Body Font**: {body}
- **Google Fonts**: {google_url}

---

## 3. Anti-Patterns to Avoid

{anti_patterns}
"""
        brand_path.write_text(brand_content, encoding="utf-8")

        tokens_dir = base_dir / "design-system" / slug
        tokens_dir.mkdir(parents=True, exist_ok=True)
        tokens_path = tokens_dir / "design-tokens.json"

        tokens = {
            "$schema": "https://design-tokens.org/schema.json",
            "primitive": {
                "color": {
                    "primary": {"$value": primary, "$type": "color"},
                    "secondary": {"$value": secondary, "$type": "color"},
                    "accent": {"$value": accent, "$type": "color"},
                    "background": {"$value": bg, "$type": "color"},
                    "foreground": {"$value": fg, "$type": "color"},
                    "card": {"$value": card, "$type": "color"},
                    "muted": {"$value": muted, "$type": "color"},
                    "border": {"$value": border, "$type": "color"},
                },
                "font": {
                    "heading": {"$value": heading, "$type": "fontFamily"},
                    "body": {"$value": body, "$type": "fontFamily"},
                },
                "spacing": {k: {"$value": v, "$type": "dimension"} for k, v in spacing.items()},
            },
            "semantic": {
                "color": {
                    "primary": {"$value": "{primitive.color.primary}", "$type": "color"},
                    "primary-foreground": {"$value": on_primary, "$type": "color"},
                    "secondary": {"$value": "{primitive.color.secondary}", "$type": "color"},
                    "accent": {"$value": "{primitive.color.accent}", "$type": "color"},
                    "background": {"$value": "{primitive.color.background}", "$type": "color"},
                    "foreground": {"$value": "{primitive.color.foreground}", "$type": "color"},
                    "card": {"$value": "{primitive.color.card}", "$type": "color"},
                    "muted": {"$value": "{primitive.color.muted}", "$type": "color"},
                    "border": {"$value": "{primitive.color.border}", "$type": "color"},
                },
            },
            "component": {
                "button": {
                    "bg": {"$value": "{semantic.color.primary}", "$type": "color"},
                    "fg": {"$value": "{semantic.color.primary-foreground}", "$type": "color"},
                },
                "card": {
                    "bg": {"$value": "{semantic.color.card}", "$type": "color"},
                    "border": {"$value": "{semantic.color.border}", "$type": "color"},
                },
            },
        }
        tokens_path.write_text(json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8")

    def _generate_design_system(
        self,
        query: str,
        project_name: str | None = None,
        output_dir: str | None = None,
        density: int | None = None,
        motion: int | None = None,
    ) -> dict | None:
        storage_root = Path(__file__).resolve().parents[3]
        target_scripts = (
            storage_root
            / "nextlevelbuilder_ui-ux-pro-max"
            / "ui-ux-pro-max"
            / "scripts"
        )
        if not target_scripts.exists():
            target_scripts = storage_root / "my_skills" / "ui-ux-pro-max" / "scripts"
        if not target_scripts.exists():
            return None

        scripts_str = str(target_scripts)
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)

        try:
            from design_system import DesignSystemGenerator, persist_design_system
            generator = DesignSystemGenerator()
            ds = generator.generate(
                query,
                project_name=project_name,
                density=density,
                motion=motion,
            )
            if output_dir:
                try:
                    persist_design_system(ds, output_dir=output_dir)
                except (OSError, ValueError, RuntimeError) as err:
                    _ = str(err)
                try:
                    self._persist_brand_and_tokens(ds, Path(output_dir))
                except (OSError, ValueError, RuntimeError) as err:
                    _ = str(err)
            return ds
        except Exception:
            return None
        finally:
            if scripts_str in sys.path:
                sys.path.remove(scripts_str)

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(
                message="❌ Error: 'destination' argument is required.",
                break_loop=False,
            )

        dest_path = Path(dest_str).resolve()
        dest_path.mkdir(parents=True, exist_ok=True)

        action = self.args.get("action", "frontend")
        if action == "chrome-extension":
            script_rel_path = "templates/chrome-extension/setup.py"
        else:
            script_rel_path = "templates/frontend/setup.py"

        resource_script = (
            Path(__file__).resolve().parent.parent / script_rel_path
        )
        if not resource_script.exists():
            return Response(
                message=f"❌ Error: setup script not found at {resource_script} (action: {action})",
                break_loop=False,
            )

        env = os.environ.copy()
        design_query = self.args.get("design_query", "")
        density_arg = self.args.get("density")
        motion_arg = self.args.get("motion")
        density = int(density_arg) if density_arg and str(density_arg).isdigit() else None
        motion = int(motion_arg) if motion_arg and str(motion_arg).isdigit() else None
        ds_info = ""

        if design_query:
            design_system = self._generate_design_system(
                design_query,
                project_name=dest_path.name,
                output_dir=str(dest_path),
                density=density,
                motion=motion,
            )
            if design_system:
                env["DESIGN_SYSTEM_JSON"] = json.dumps(design_system, ensure_ascii=False)
                ds_info = f"\n🧠 Design system generated for: \"{design_query}\""
            else:
                ds_info = "\n⚠️ ui-ux-pro-max skill not found. Scaffolding without custom theme."

        try:
            result = subprocess.run(
                ["python3", "-u", str(resource_script)],
                cwd=str(dest_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=2400,
            )

            if result.returncode == 0:
                return Response(
                    message=(
                        f"✅ SetUI successful in {dest_path}{ds_info}\n\n"
                        f"Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )
            else:
                return Response(
                    message=(
                        f"❌ SetUI failed with exit code {result.returncode}\n\n"
                        f"Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )

        except subprocess.TimeoutExpired as e:
            partial = e.stdout or "" if hasattr(e, "stdout") else ""
            return Response(
                message=(
                    f"❌ SetUI timed out after 40 minutes.\n"
                    f"Partial output:\n{partial[-500:]}\n\n"
                    f"Hint: Check npm/network connectivity."
                ),
                break_loop=False,
            )
        except Exception as e:
            return Response(
                message=f"❌ Error running SetUI: {str(e)}",
                break_loop=False,
            )
