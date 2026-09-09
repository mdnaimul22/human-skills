import os
import sys
import json
import base64
import asyncio
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR
for p in [_CURRENT_DIR, *_CURRENT_DIR.parents]:
    if (p / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p
        break
    if (p / "skills" / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p / "skills"
        break
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))

from helpers.tool import Tool, Response


class MermaidView(Tool):
    """
    Standalone tool to convert Mermaid diagram code into high-fidelity SVG or PNG preview images.
    Supports online high-speed rendering with automatic local mmdc CLI installation and offline execution.
    """
    name = "mermaid_view"
    description = "Converts Mermaid diagram code into high-fidelity PNG or SVG preview images."
    arguments = {
        "diagram_code": "Mermaid diagram code string (REQUIRED).",
        "path": "Target directory or output file path where the rendered image will be saved. Defaults to current directory.",
        "preview": "Output format: 'png' (default) or 'svg'.",
        "file_name": "Optional custom file name (e.g. 'architecture.png'). Defaults to 'diagram.{preview}'.",
        "theme": "Optional Mermaid theme: 'default', 'dark', 'neutral', 'forest', 'base'. Default: 'default'."
    }
    instruction = "For detailed skill instructions run: human-skills --skill_info mermaid-view"

    @staticmethod
    def _sanitize_diagram_code(raw_code: str) -> str:
        """Strip markdown fences (```mermaid ... ```) if present."""
        code = raw_code.strip()
        if code.startswith("```"):
            lines = code.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        return code

    @staticmethod
    async def _render_via_api(code: str, fmt: str, theme: str) -> bytes:
        """Render mermaid diagram via high-speed API engine."""
        payload = {
            "code": code,
            "mermaid": {
                "theme": theme
            }
        }
        json_str = json.dumps(payload)
        b64 = base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("ascii")

        if fmt == "svg":
            url = f"https://mermaid.ink/svg/{b64}"
        else:
            url = f"https://mermaid.ink/img/{b64}?type=png"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            }
        )

        loop = asyncio.get_running_loop()

        def _fetch():
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read()

        return await loop.run_in_executor(None, _fetch)

    @classmethod
    def _is_mermaidx_installed(cls) -> bool:
        """Check whether the pure-Python mermaidx engine is available."""
        try:
            import mermaidx  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    async def _install_mermaidx(cls) -> Tuple[bool, str]:
        """Silently auto-install mermaidx via pip in the current Python environment."""
        loop = asyncio.get_running_loop()
        cmd = [sys.executable, "-m", "pip", "install", "mermaidx"]

        def _install():
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    return True, "Installed successfully"
                return False, res.stderr or res.stdout or f"pip install returned code {res.returncode}"
            except Exception as e:
                return False, str(e)

        return await loop.run_in_executor(None, _install)

    @classmethod
    async def _render_via_mermaidx(cls, code: str, fmt: str, theme: str) -> Tuple[Optional[bytes], str]:
        """
        Renders Mermaid code into PNG or SVG in-memory using pure-Python mermaidx (QuickJS + resvg).
        Zero browser overhead, zero Node.js, ultra-fast.
        """
        loop = asyncio.get_running_loop()

        def _run():
            try:
                import mermaidx
                opts: Dict[str, Any] = {}
                if theme in ("default", "dark", "forest", "neutral", "base"):
                    opts["theme"] = theme

                diag = mermaidx.render(code, **opts)
                if fmt == "svg":
                    svg_content = diag.svg()
                    data = svg_content.encode("utf-8") if isinstance(svg_content, str) else svg_content
                else:
                    data = diag.png()
                return data, ""
            except Exception as exc:
                return None, str(exc)

        return await loop.run_in_executor(None, _run)

    @classmethod
    def _find_local_mmdc(cls) -> Optional[str]:
        """Check whether mmdc is installed in PATH or standard Node/NVM directories."""
        bin_path = shutil.which("mmdc")
        if bin_path:
            return bin_path

        home = Path.home()
        candidates = [
            home / ".nvm" / "versions" / "node",
            home / ".npm-global" / "bin",
            home / ".local" / "bin",
            Path("/usr/local/bin"),
            Path("/usr/bin")
        ]
        for candidate in candidates:
            if candidate.is_dir():
                direct = candidate / "mmdc"
                if direct.is_file() and os.access(direct, os.X_OK):
                    return str(direct)
                if "node" in candidate.name:
                    try:
                        for node_dir in sorted(candidate.iterdir(), reverse=True):
                            bin_file = node_dir / "bin" / "mmdc"
                            if bin_file.is_file() and os.access(bin_file, os.X_OK):
                                return str(bin_file)
                    except OSError:
                        pass
        return None

    @classmethod
    def _check_local_mmdc(cls) -> Tuple[bool, Optional[str]]:
        """Verifies whether mmdc CLI is installed locally."""
        bin_path = cls._find_local_mmdc()
        if bin_path and os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
            return True, bin_path
        return False, None

    @classmethod
    async def _install_local_mmdc(cls) -> Tuple[bool, str]:
        """Auto-installs @mermaid-js/mermaid-cli via npm as secondary fallback."""
        npm_bin = shutil.which("npm")
        if not npm_bin:
            home = Path.home()
            nvm_node = home / ".nvm" / "versions" / "node"
            if nvm_node.is_dir():
                try:
                    for node_dir in sorted(nvm_node.iterdir(), reverse=True):
                        cand_npm = node_dir / "bin" / "npm"
                        if cand_npm.is_file() and os.access(cand_npm, os.X_OK):
                            npm_bin = str(cand_npm)
                            break
                except OSError:
                    pass

        if not npm_bin:
            return False, "npm command not found in system PATH or NVM directories."

        install_cmd = [npm_bin, "install", "-g", "@mermaid-js/mermaid-cli"]
        loop = asyncio.get_running_loop()

        def _install():
            try:
                env = dict(os.environ)
                if shutil.which("google-chrome") or shutil.which("google-chrome-stable"):
                    env["PUPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "true"
                res = subprocess.run(install_cmd, capture_output=True, text=True, timeout=180, env=env)
                if res.returncode == 0:
                    return True, "Installed successfully"
                return False, res.stderr or res.stdout or f"npm install returned exit code {res.returncode}"
            except Exception as e:
                return False, str(e)

        return await loop.run_in_executor(None, _install)

    @classmethod
    async def _render_via_local_cli(cls, code: str, out_file: Path, theme: str = "default") -> Tuple[bool, str]:
        """Renders diagram locally via mermaid-cli (mmdc) as secondary fallback."""
        is_installed, mmdc_bin = cls._check_local_mmdc()
        if not is_installed or not mmdc_bin:
            installed_ok, install_msg = await cls._install_local_mmdc()
            if not installed_ok:
                return False, f"Local mmdc CLI not installed and auto-installation failed: {install_msg}"
            is_installed, mmdc_bin = cls._check_local_mmdc()
            if not is_installed or not mmdc_bin:
                return False, "Auto-installation completed, but mmdc executable was not found."

        tmp_in = out_file.parent / f"_temp_input_{out_file.stem}.mmd"
        tmp_puppeteer = out_file.parent / f"_temp_puppeteer_{out_file.stem}.json"
        try:
            tmp_in.write_text(code, encoding="utf-8")

            puppeteer_config: dict[str, Any] = {
                "args": ["--no-sandbox", "--disable-setuid-sandbox"]
            }
            chrome_candidates = [
                shutil.which("google-chrome"),
                shutil.which("google-chrome-stable"),
                shutil.which("chromium"),
                shutil.which("chromium-browser"),
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser"
            ]
            for cand in chrome_candidates:
                if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                    puppeteer_config["executablePath"] = cand
                    break

            tmp_puppeteer.write_text(json.dumps(puppeteer_config), encoding="utf-8")

            cmd = [
                mmdc_bin,
                "-i", str(tmp_in),
                "-o", str(out_file),
                "-p", str(tmp_puppeteer)
            ]
            if theme in ("default", "dark", "forest", "neutral", "base"):
                cmd.extend(["-t", theme])

            loop = asyncio.get_running_loop()

            def _run():
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if res.returncode == 0:
                    return True, ""
                return False, res.stderr or res.stdout or f"mmdc exited with code {res.returncode}"

            return await loop.run_in_executor(None, _run)
        except Exception as exc:
            return False, str(exc)
        finally:
            for f in (tmp_in, tmp_puppeteer):
                if f.exists():
                    try:
                        f.unlink()
                    except OSError:
                        pass

    @classmethod
    async def _render_locally(cls, code: str, out_file: Path, fmt: str, theme: str = "default") -> Tuple[Optional[bytes], str]:
        """
        Local rendering coordinator:
          1. Tries pure-Python mermaidx (QuickJS + resvg) -> Zero browser, in-process, ~0.8s.
          2. Auto-installs mermaidx via pip if missing.
          3. Falls back to mmdc CLI if mermaidx fails.
        """
        # 1. mermaidx (Pure Python, QuickJS + Rust resvg)
        if not cls._is_mermaidx_installed():
            await cls._install_mermaidx()

        if cls._is_mermaidx_installed():
            data, err = await cls._render_via_mermaidx(code, fmt, theme)
            if data:
                return data, ""

        # 2. Secondary fallback: mmdc CLI
        cli_ok, cli_err = await cls._render_via_local_cli(code, out_file, theme)
        if cli_ok and out_file.exists():
            return out_file.read_bytes(), ""

        return None, cli_err or "Local rendering failed"

    async def execute(self, **kwargs) -> Response:
        diagram_code = self.args.get("diagram_code")
        if not diagram_code or not str(diagram_code).strip():
            return Response(
                message="❌ Error: 'diagram_code' argument is required and cannot be empty.\n"
                        "💡 Example:\n"
                        'human-skills \'{"tool_name": "mermaid_view", "tool_args": {"diagram_code": "graph TD; A-->B;", "preview": "png"}}\'',
                break_loop=False
            )

        clean_code = self._sanitize_diagram_code(str(diagram_code))
        fmt = str(self.args.get("preview", "png")).lower().strip()
        if fmt not in ("png", "svg"):
            return Response(
                message=f"❌ Error: Invalid preview format '{fmt}'. Allowed formats are 'png' or 'svg'.",
                break_loop=False
            )

        theme = str(self.args.get("theme", "default")).lower().strip()
        raw_path = self.args.get("path")
        custom_file = self.args.get("file_name")

        if not raw_path:
            dest_dir = Path.cwd()
            filename = custom_file if custom_file else f"diagram.{fmt}"
            out_file = dest_dir / filename
        else:
            p = Path(raw_path).expanduser().resolve()
            if p.suffix.lower() in (".png", ".svg"):
                out_file = p
                fmt = p.suffix.lower()[1:]
                dest_dir = p.parent
            else:
                dest_dir = p
                filename = custom_file if custom_file else f"diagram.{fmt}"
                out_file = dest_dir / filename

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return Response(
                message=f"❌ Error: Failed to create target directory '{dest_dir}': {e}",
                break_loop=False
            )

        rendered_bytes: Optional[bytes] = None
        error_details = ""

        # 1. Primary Engine: High-speed render API
        try:
            rendered_bytes = await self._render_via_api(clean_code, fmt, theme)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                error_body = ""
            error_details = f"HTTP {e.code}: {e.reason}. {error_body}".strip()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            error_details = f"Network/Internet unavailable ({e})"
        except Exception as e:
            error_details = str(e)

        # 2. Secondary Engine: Silent Local Fallback (mermaidx + mmdc backup)
        # If internet is not available or online API fails:
        # Uses pure-Python mermaidx (QuickJS + Rust resvg) -> Zero browser, in-process, ~0.8s.
        if not rendered_bytes:
            local_bytes, local_err = await self._render_locally(clean_code, out_file, fmt, theme)
            if local_bytes:
                rendered_bytes = local_bytes
            else:
                if local_err:
                    error_details += f"\nLocal Render Error: {local_err}"

        if not rendered_bytes:
            return Response(
                message=f"❌ Mermaid Render Error: Failed to render diagram.\n"
                        f"Details: {error_details}\n\n"
                        f"💡 Please check your Mermaid syntax. Input preview:\n"
                        f"--------------------------------------------------\n"
                        f"{clean_code[:300]}...",
                break_loop=False
            )

        # Write output file if not already created by local CLI
        try:
            if not out_file.exists():
                out_file.write_bytes(rendered_bytes)
        except Exception as e:
            return Response(
                message=f"❌ Error writing output file '{out_file}': {e}",
                break_loop=False
            )

        file_size_kb = len(rendered_bytes) / 1024.0
        size_str = f"{file_size_kb:.1f} KB" if file_size_kb >= 1 else f"{len(rendered_bytes)} B"

        msg_lines = [
            "✅ Mermaid Diagram Successfully Rendered!",
            "──────────────────────────────────────────────────────────",
            f"  📂 Output File : {out_file}",
            f"  📊 Format      : {fmt.upper()}",
            f"  📏 File Size   : {size_str}",
            f"  🎨 Theme       : {theme}",
            "──────────────────────────────────────────────────────────",
            f"💡 Clickable Link: file://{out_file}"
        ]

        return Response(
            message="\n".join(msg_lines),
            break_loop=False,
            additional={
                "output_file": str(out_file),
                "format": fmt,
                "size_bytes": len(rendered_bytes)
            }
        )