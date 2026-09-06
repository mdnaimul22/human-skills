---
trigger: always_on
name: coding_standards
description: Core coding principles focused on Clean Architecture, Type Safety, and Performance.
---

# Coding Standards

> *"We build scalable infrastructure, not just scripts. So The Structure is not an optional parameter — it's the foundation."*

You don't like messy Spaghetti code at all. The layout of the project will be **modern schema-based, lean & flat** — centered on `src/`. 

Where the responsibilities of each module like core, providers, tools, helpers and config will be clearly separated through the **Single Responsibility Principle (SRP)**.

> [!CAUTION]  
> ❌ Spaghetti code, God classes, and implicit dependencies are completely prohibited.

---

## 1. The Core Vision (Clean Architecture)

> [!NOTE]  
> *"Maintainable Code structure that reads like a premium framework."*

The code must look like it is part of a **solid, production-grade framework.**

- **Naming** — The purpose can be understood simply by reading the variable/function/class name.
!- **DRY** — No duplication, utilize abstraction.
!- **SOLID** — Always applicable.
- **No dead code** — Unused imports and stale variables are strictly prohibited.
- **Consistency** — Same pattern and same style must be maintained throughout the codebase.

> [!TIP]  
> 🎯 **Standard:** Any team member, senior or junior, should immediately understand what is happening, why it is happening, and where to extend it just by looking at the code.

---

## 2. Coding Guidelines (Safety, Performance, Robustness)

### 2.1 Type Safety

> [!WARNING]  
> **Ambiguity kills maintainability.**

Always utilize **Pydantic models** and Python **Type Hints**.
The code must be completely **`mypy` / `pyright` error-free**.

```python
# ❌ Avoid
data: dict = {}
value: Any = get_value()

# ✅ Prefer
data: UserConfig = UserConfig(...)
value: ResponsePayload = get_value()
```

> If using raw `dict` or `Any` is unavoidable, there must be a clear and explicit justification.

### 2.2 Boundary Defense & Null Elimination (The Tony Hoare Rule)

> *"I call it my billion-dollar mistake. It was the invention of the null reference in 1965." — Sir Tony Hoare*  
> **"Don't check for None repeatedly — eliminate None at the boundary."**

Never allow defensive, repetitive `None` checks to pollute core business logic.

- **Sanitize at the Perimeter (Null Object Pattern):** When receiving optional or external data at module boundaries, resolve them immediately to a safe, typed default (e.g., `canvas = template.canvas if (template and template.canvas) else CanvasConfig()`).
- **Guaranteed Invariants Inside the Core:** Once past the entry boundary, assume entities are valid, non-null objects. Core logic should never fear `None`.
- **Prohibited:** Never scatter `obj.field if obj else default` across downstream calculations or rendering passes.

```python
# ❌ Avoid (Noisy defensive checks polluting business logic)
def process(context):
    mode = context.canvas.mode if context.canvas else "blur"
    intensity = context.canvas.blur_intensity if context.canvas else 30
    darken = context.canvas.darken_alpha if context.canvas else 0.25

# ✅ Prefer (Tony Hoare Boundary Defense / Null Object Pattern)
def process(context):
    # Eliminate None once at the entry boundary:
    canvas = context.template.canvas if (context.template and context.template.canvas) else CanvasConfig()

    # Pure business logic — zero null-checking noise:
    mode = canvas.mode
    intensity = canvas.blur_intensity
    darken = canvas.darken_alpha
```

### 2.3 Performance & Determinism
> *"Fast by design, not by accident."*

The system design will be **ultra-fast** and must follow an **extensible pattern** in all scenarios.

- [ ] Adding a new provider requires zero modifications to the core.
- [ ] Configuration-driven behavior — hardcoded values are prohibited.
- [ ] Async-first — always use `async/await` for I/O bound operations.
- [ ] Implement lazy loading wherever applicable.

### 2.4 Robustness
> *"New features must land on solid ground."*

Adding a new feature = **existing code remains untouched**, only new modules/layers are extended.

> `Schema First → Clean Interfaces → Stable Core → Safe Extensions`

**Every component must possess:**
- [ ] Structured error handling (`try/except` with typed exceptions).
- [ ] Meaningful logging — `print()` is prohibited. Consolidate logs by layer (e.g., `service.log`, `router.log`) instead of per-script.
- [ ] Graceful degradation — a single failure will not bring down the entire system.

