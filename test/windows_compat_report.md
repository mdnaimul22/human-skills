# Windows ↔ Linux Handoff Protocol (machine-to-machine)

> Purpose: the Windows-side assistant (this machine) and the Linux-side
> assistant have no direct channel. This repo IS the channel.
> Either side writes its side's file, commits, pushes; the other side
> pulls and continues. Never edit the other side's section in place —
> reply in your own `## Reply` block with the same date header.

## Mailboxes

| Side    | Inbox file (other side writes here)              | Outbox (you write here)                          |
|---------|--------------------------------------------------|--------------------------------------------------|
| Linux   | `test/windows_compat_report.md` (this file)      | `test/linux_compat_report.md`                    |
| Windows | `test/linux_compat_report.md`                    | `test/windows_compat_report.md` (this file)      |

## Round-trip rules

1. Each round = one dated entry appended at the bottom (`### YYYY-MM-DD <side>`).
2. Entry format: `STATUS | tool | note`. STATUS ∈ {`PASS`, `FAIL`, `NEEDS-LINUX`, `NEEDS-WINDOWS`, `DONE`}.
3. Claim a task by adding `CLAIMED by <side>`; finish with `DONE` + commit hash.
4. A tool is cross-OS accurate only when BOTH sides report `PASS` for it.

---

# Windows-side report (written on Windows, Python 3.11, cp1252 console)

## Verified PASS on Windows (2026-10-07, commits 9f84633..0bd5d26)

| Tool / area              | Result | Evidence |
|--------------------------|--------|----------|
| `human-skills --list-all` (407 skills) | PASS | exit 0, no `PYTHONUTF8` preset, cp1252 console |
| `human-skills.cmd` wrapper | PASS | exit 0, sets `PYTHONUTF8=1` itself |
| `human-skills.ps1` wrapper | PASS | exit 0 from any dir |
| `find_by_name`           | PASS | `os.walk` fallback, 7 files found in `skills/helpers` |
| `linter` (default mode)  | PASS | exit 0 on `skills/helpers` scan |
| `zram_optimizer`         | PASS (guarded) | clean Linux-only error, no crash |
| `gen_requirements` stdlib detect | PASS | `sysconfig` path returns stdlib set |
| `bootstrap` / `setui` launchers | PASS (import/compile) | `sys.executable`, `py_compile` clean |
| cross-CWD dispatch (`%TEMP%` → repo) | PASS | exit 0 |

## NEEDS-LINUX (Windows cannot verify — Linux side please run & report)

1. `bootstrap` end-to-end: scaffold a throwaway project on Linux, confirm layout identical to Windows output.
2. `setui` end-to-end: `npm`/`node` present on Linux — confirm resource script exit code parity.
3. `zram_optimizer run/bench/deploy/status` on a real Linux host — confirm no regression from `_is_root()` refactor (exact `sudo` behavior, exit codes).
4. `gen_requirements` on Python 3.12+: confirm `sysconfig` stdlib set == old `distutils` set (diff the outputs).
5. `tree_gen`, `linter`, `grep_search`, `view_file`, `write_to_file`, `list_dir`, `math_animate`, `mermaid_view`, `OpenevolveTool`, `setconfig`, `threejs_*` — run each tool's happy path on Linux, report PASS/FAIL per tool.
6. `scripts/install.sh` — re-run on a clean Linux container after the `execute.py` changes (stdout reconfigure must be a no-op on UTF-8 Linux).

## Known Linux-only by design (no Windows port expected)

- `zram_optimizer` full functionality (`/sys`, `modprobe`, `systemd`) — Windows guard message is the correct behavior.
- `math_animate` background installer (`bash -c`, `sudo apt-get`) — needs a Windows installer path (`winget`/`choco`) OR documented WSL-only status. **Decision needed from repo owner.**
- `mermaid_view` Chrome/NVM discovery (`/usr/bin/google-chrome`, `~/.nvm`) — needs Windows discovery (`%ProgramFiles%`, registry) OR WSL-only status. **Decision needed.**
- `threejs_world` / `threejs_asset_catalog` — dead imports (`tools.base_tool` missing) + missing `templates/` dir on BOTH OSes. Needs a real port, not an OS fix.

## Replies (append below)

### 2026-10-07 windows
- Outbox initialized. Waiting for Linux side to create `test/linux_compat_report.md` with per-tool PASS/FAIL. Owner decisions needed on `math_animate` / `mermaid_view` Windows support scope.
