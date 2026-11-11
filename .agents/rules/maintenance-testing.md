---
trigger: always_on
name: maintenance_testing
description: Strict guidelines for File-by-File Sub-Atomic Refactoring, Isolated Orchestrator Architecture, Mirrored Fast Testing, and Token Discipline.
---

# Maintenance, Refactoring & Verification Standards

## 1. Strict Command Scope & Token Discipline
- Execute **only** what the user explicitly asks in the current turn.
- Never jump ahead to the next file or run unrequested background analyses before the current step is confirmed.

## 2. Isolated Sub-Engines & Single Orchestrator Endpoint
- **Private Worker Directory (`src/core/<domain>/`)**: Contains strictly isolated, single-responsibility sub-engine files. Never place the public manager inside this folder or import internal workers outside the domain.
- **Single Public Orchestrator (`src/core/<domain>_manager.py`)**: Acts as the sole public endpoint for the domain. External modules must only import from `src/core/<domain>_manager.py` and interact via an explicit Consumer Contract (`start()`, `stop()`, and closed-loop feedback hooks).

## 3. The 5-Step File-by-File Engineering Loop
Never modify multiple sub-engines blindly at once. Process one file at a time through this exact loop:
1. **Post-Mortem & Workflow Design**: Analyze (a) how the file currently works, (b) hidden bugs, kernel/OS edge cases, race conditions, and sync/async requirements, and (c) how the target sub-atomic workflow should work. Stop and wait for user approval.
2. **Clean Implementation**: After approval, implement the file with zero comments/docstrings and strict types (no `Any`).
3. **AST Linter Gate**: Run `human-skills` `linter` on the file and resolve all violations (`0 violations`).
4. **Immediate Sub-Engine Test & Mandatory Timing Report**: Write and run `PYTHONPATH=. pytest tests/<domain>/test_<file>.py -v --durations=0`. Always explicitly report both the individual test execution durations, the total `pytest` process elapsed time, and confirmation of zero regressions across the whole repository suite.
5. **Next File Gate**: Move to the next file only after the current file's implementation, linter audit, and test timing are verified.

## 4. Mirrored Ultra-Fast Test Architecture
- **No Bloated Global Fixtures**: Unit tests must never trigger global database creation or full FastAPI app imports unless explicitly testing routers/DB.
- **PEP 562 Package Lazy Loading (`__getattr__`)**: Top-level package `__init__.py` files (`src/core/__init__.py`, `src/helpers/__init__.py`) must use lazy `importlib.import_module` + `module.__dict__[name]` lookup so importing a single sub-engine never triggers heavy third-party imports (`yt_dlp`, `cv2`, `sqlalchemy`, `fastapi`).
- **Sub-Engine Lifecycle Tests (`tests/core/<domain>/test_<worker>.py`)**: Test each internal worker engine independently in milliseconds.
- **Orchestrator Lifecycle Test (`tests/core/<domain>_manager.py`)**: Test the full end-to-end autonomous lifecycle of the orchestrator after all sub-engines are verified.

