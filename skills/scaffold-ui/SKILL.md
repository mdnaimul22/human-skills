---
name: scaffold-ui
description: Scaffolds a complete Next.js + shadcn/ui + Tailwind CSS frontend with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client. Bridges with ui-ux-pro-max for AI-powered custom themes.
---

# Scaffold UI
> *"One command. Full frontend. Intelligent theming."*

Scaffolds a complete **Next.js + shadcn/ui + Tailwind CSS** frontend layer (`web/`) with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client.

## Why This Exists

Modern web applications require a clear architectural boundary: the **backend owns all business logic, validation, and data**, and the **frontend is purely a presentation layer**. In practice, this boundary is frequently violated — developers duplicate validation logic, re-implement service-layer concerns in Next.js Route Handlers, or treat the frontend as a second backend. This erodes the single source of truth and creates maintenance debt across every project.

This skill enforces that boundary structurally.

SetUI scaffolds a Next.js frontend that is **deliberately thin** — it has no database access, no business logic, and no validation rules. Its sole responsibility is to call the FastAPI backend and render responses. All intelligence lives in FastAPI where it belongs: Pydantic schemas define the contract, service layers own the logic, and routers expose the interface.

The result is an architecture where:
- **FastAPI** is the system — auth, validation, data, business rules
- **Next.js** is the face — layout, navigation, UI state, API calls only
- **New projects** start from a proven skeleton, not from scratch
- **Existing backend investment** is never duplicated or second-guessed

This is not a full-stack framework. It is a disciplined frontend layer designed to complement a production FastAPI backend.

## How to Use

### Basic (9 built-in themes)

```bash
human-skills '{"tool_name": "setui", "tool_args": {"destination": "/path/to/project"}}'
```

### With AI Design System (bridge to ui-ux-pro-max)

```bash
human-skills '{"tool_name": "setui", "tool_args": {
    "destination": "/path/to/project",
    "design_query": "beauty spa wellness premium"
}}'
```

When `design_query` is provided:
1. **ui-ux-pro-max** generates a complete design system (colors, fonts, style)
2. A custom `[data-theme="custom"]` CSS block is injected into `globals.css`
3. Google Fonts `<link>` tags are added to `layout.tsx`
4. `--font-sans` is patched with the recommended font pairing
5. Default theme is set to `"custom"`

> All 9 built-in themes remain available. The custom theme is additive.

---

## What SetUI Creates

```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx              ← Root layout + ThemeProvider
│   │   ├── globals.css             ← 9 themes + custom AI theme + shadcn vars
│   │   ├── (auth)/                 ← Auth pages (no sidebar/navbar)
│   │   │   ├── layout.tsx          ← Centered card layout
│   │   │   └── login/page.tsx      ← OAuth + email/password form
│   │   └── (dashboard)/            ← Dashboard pages (with sidebar/navbar)
│   │       ├── layout.tsx          ← Sidebar + Navbar wrapper
│   │       └── page.tsx            ← Dashboard home
│   │
│   ├── components/
│   │   ├── ui/                     ← shadcn components (30+ auto-installed)
│   │   ├── layout/
│   │   │   ├── sidebar.tsx         ← Collapsible sidebar
│   │   │   ├── navbar.tsx          ← Top bar
│   │   │   ├── page-header.tsx     ← Page title + action buttons
│   │   │   └── theme-switcher.tsx  ← Theme dropdown (9+1 themes)
│   │   └── auth/
│   │       └── login-form.tsx      ← OAuth buttons
│   │
│   ├── lib/
│   │   ├── api.ts                  ← Secure FastAPI client
│   │   └── utils.ts                ← cn() utility
│   │
│   ├── hooks/
│   │   └── use-sidebar.ts          ← Sidebar state (Zustand)
│   │
│   └── types/
│       └── api.ts                  ← OpenAPI auto-gen placeholder
│
├── scripts/
│   └── generate-types.sh
├── components.json
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

---

## Theme System

9 built-in themes + 1 optional AI-generated custom theme:

| Theme | Accent | Type |
|:---|:---|:---|
| Default Dark | Blue | 🌙 Dark |
| Matrix | Green | 🌙 Dark |
| Monokai | Lime | 🌙 Dark |
| VS Code | Blue | 🌙 Dark |
| Dracula | Purple | 🌙 Dark |
| One Dark | Blue | 🌙 Dark |
| Nord | Cyan | 🌙 Dark |
| Clear Ice | Deep Blue | ☀️ Light |
| Snow | Blue | ☀️ Light |
| **Custom** | **AI-generated** | **Auto-detected** |

### Three-Layer Token Architecture

```
Theme Definition (raw)    →  --accent: #10b981
         ↓
Bridge Mapping (auto)     →  --color-primary: var(--accent)
         ↓
shadcn/ui Mapping (auto)  →  --primary: var(--color-primary)
```

---

## Arguments

| Argument | Required | Description |
|:---|:---|:---|
| `destination` | ✅ | Project root path |
| `design_query` | ❌ | Product/industry query for AI theme generation |

### design_query Examples

| Query | What AI generates |
|:---|:---|
| `"beauty spa wellness"` | Soft pinks, sage greens, elegant serif fonts |
| `"fintech crypto dashboard"` | Dark mode, sharp blues, monospace accents |
| `"SaaS analytics platform"` | Professional blues, clean sans-serif |
| `"gaming esports"` | Neon accents, cyberpunk style, dark base |

---

## Post-Scaffolding

1. `cd web && npm install && npm run dev` → Open http://localhost:3000
2. Add `NEXT_PUBLIC_API_URL=http://localhost:8000` to `web/.env.local`
3. Generate types: `bash web/scripts/generate-types.sh`
4. Edit `NAV_ITEMS` in `sidebar.tsx` to add navigation links
5. Add new pages under `app/(dashboard)/`

---

## Development Contract (Post-Scaffolding Rules)

> [!CAUTION]
> **MANDATORY: Read Before Write.**
> Before writing ANY new component, hook, store, or page in a scaffolded project, you **MUST** first read and understand **every existing file** the scaffold created. The scaffold is a complete, interconnected skeleton — not a blank canvas. Writing without reading leads to duplicated components, conflicting layouts, and wasted tokens.

> [!IMPORTANT]
> **Gun-Point Principle: All new code sits ON TOP of the scaffold — never beside it.**
> The scaffold provides a production-grade layout system (AppShell, Sidebar, Navbar, Settings, Toast, Theme). Your job is to **customize and extend** these existing components for your project — not to create parallel replacements. Every new component must integrate into the existing composition tree. If you find yourself creating a new sidebar, a new navbar, or a new route group layout, **you are doing it wrong**. Modify what exists. Don't spread the code.

### Step 0 — Mandatory File Audit

Before any development work begins on a scaffolded project, execute this checklist:

```
READ EVERY FILE — no exceptions:
  □ src/app/layout.tsx                    ← Root layout, ThemeProvider, fonts
  □ src/app/globals.css                   ← All 9 themes, bridge mapping, shadcn vars
  □ src/app/(dashboard)/layout.tsx        ← AppShell wrapper — THIS is your main layout
  □ src/app/(dashboard)/page.tsx          ← Dashboard home — extend this
  □ src/app/(auth)/layout.tsx             ← Auth layout (centered card)
  □ src/app/(auth)/login/page.tsx         ← Login page
  □ src/app/not-found.tsx                 ← 404 page
  □ src/components/layout/app-shell.tsx   ← Sidebar + Navbar composition
  □ src/components/layout/sidebar.tsx     ← Collapsible sidebar with NAV_ITEMS
  □ src/components/layout/navbar.tsx      ← Top bar with title/actions slots
  □ src/components/layout/header.tsx      ← Page header (title + action buttons)
  □ src/components/layout/settings.tsx    ← Font/Scale/Theme settings panel
  □ src/components/layout/theme.tsx       ← ThemeLoadedScript + ThemeSwitcher
  □ src/components/layout/toast.tsx       ← Toast notification system (useToast)
  □ src/hooks/use-sidebar.ts             ← Sidebar Zustand store
  □ src/hooks/use-mobile.ts              ← Mobile breakpoint hook
  □ src/lib/api.ts                       ← Secure FastAPI client (apiFetch)
  □ src/lib/utils.ts                     ← cn() utility
  □ src/types/api.ts                     ← OpenAPI auto-gen placeholder
```

Only after completing this audit may you proceed to write new code.

### Component Composition Map

The scaffold's layout components form a strict composition tree. Understand this before touching anything:

```
RootLayout (app/layout.tsx)
  └── ThemeProvider + ThemeLoadedScript + ToastContainer
       │
       ├── (auth)/layout.tsx → Centered card, NO sidebar/navbar
       │    └── login/page.tsx → LoginForm
       │
       └── (dashboard)/layout.tsx → AppShell wrapper ← YOUR MAIN ENTRY POINT
            │
            └── AppShell (components/layout/app-shell.tsx)
                 ├── Sidebar (components/layout/sidebar.tsx)
                 │    ├── NAV_ITEMS[] → navigation links (edit this!)
                 │    ├── SettingsPanel → font/scale/theme controls
                 │    └── Resize handle → drag-to-resize
                 │
                 ├── Navbar (components/layout/navbar.tsx)
                 │    ├── title prop → page title
                 │    ├── description prop → subtitle
                 │    └── actions prop → right-side buttons (slot)
                 │
                 └── {children} → YOUR PAGE CONTENT GOES HERE
```

### Rule 1 — Extend `(dashboard)`, Never Create Parallel Route Groups

> [!WARNING]
> **FORBIDDEN:** Creating new route groups like `(studio)/`, `(editor)/`, `(workspace)/` alongside `(dashboard)/`.
> This fragments the layout, duplicates chrome, and creates routing conflicts.

The `(dashboard)` route group IS your application shell. It already provides sidebar, navbar, settings, and theme integration. All your application pages belong inside it.

**Correct approach:**

```
app/(dashboard)/
├── layout.tsx          ← Already has AppShell — DO NOT recreate
├── page.tsx            ← Your landing/home page — customize this
├── editor/page.tsx     ← Add new pages as subdirectories
├── settings/page.tsx   ← More pages here
└── mint/page.tsx       ← And here
```

If a page needs a different layout (e.g., no sidebar, fullscreen canvas), control it via **props and conditional rendering** inside the existing AppShell, NOT by creating a separate route group.

### Rule 2 — Customize Existing Components, Don't Duplicate

| Need | ✅ Correct | ❌ Forbidden |
|:---|:---|:---|
| Custom navigation | Edit `NAV_ITEMS[]` in `sidebar.tsx` | Creating `my-sidebar.tsx` |
| Page-specific toolbar | Pass `actions` prop to `Navbar` | Creating `my-navbar.tsx` |
| Brand/logo change | Edit the header in `sidebar.tsx` | Creating `studio-navbar.tsx` |
| New notification | Use `useToast().add()` from `toast.tsx` | Creating custom toast system |
| Theme customization | Add `[data-theme="custom"]` in `globals.css` | Hardcoding colors inline |
| Right-side panel | Add panel as child inside `AppShell` page | Creating parallel layout |
| Full-width page | Pass layout props to `AppShell` | Bypassing `AppShell` entirely |

### Rule 3 — Token System Is Sacred

All styling MUST use the scaffold's CSS custom properties. Never hardcode colors.

```tsx
// ✅ Correct — uses theme tokens
className="bg-[var(--color-surface)] text-[var(--color-text)] border-[var(--color-border)]"

// ❌ Forbidden — hardcoded colors that break on theme switch
className="bg-[#0a0a0a] text-white border-white/5"
```

### Rule 4 — API Client Is Pre-Built

`src/lib/api.ts` provides `apiFetch<T>()` with timeout, error handling, and cookie auth.
**Extend it** (add new methods like `apiFetchRaw`) — don't replace it.

```tsx
// ✅ Extend the existing api.ts
export async function apiFetchRaw(endpoint: string, options?: RequestInit): Promise<string> { ... }
export const api = { ...existingMethods, postRaw: ... }

// ❌ Don't create a new api client file
// ❌ Don't use raw fetch() bypassing apiFetch
```

---

## Hydration & Persistence Gotchas

> [!CAUTION]
> **Production-Tested Patterns.** These patterns were discovered during production debugging of ChainCV. Ignoring them leads to subtle 20ms UI flashes on page reload, stale localStorage crashes, and invisible-text bugs across themes. Every scaffold-ui project inherits these patterns — understand them before writing client-side code.

### Gotcha 1 — DOM Mutation Hygiene (Hydration Flash)

The `useApplySettings()` hook applies font/scale to `<html>`. **Never unconditionally mutate the DOM when the value equals the browser default.**

```tsx
// ❌ WRONG — causes unnecessary reflow even when value === default
document.documentElement.style.fontSize = scale.size;  // "16px" = browser default!

// ✅ CORRECT — only touch DOM when value differs from default
if (scaleKey !== DEFAULT_SCALE_KEY) {
    html.style.fontSize = scale.size;
} else {
    html.style.removeProperty("font-size");  // let browser default take over
}
```

**Why this matters:** After Next.js hydration, Zustand `persist` restores state from localStorage and triggers `useEffect`. If the restored value is the default (`"m"` → `16px`), setting `fontSize = "16px"` is a no-op semantically but still triggers:
1. DOM attribute mutation → MutationObserver callbacks
2. Style recalculation → layout reflow
3. **Visible 20ms flash** as the browser recalculates all rem-based layouts

The fix: compare against defaults first. Remove inline styles when reverting to defaults. Clean up empty `style` attributes.

### Gotcha 2 — Zustand Persist Versioning

**Always add `version` and `migrate` to persisted stores.** Without versioning, any change to the store shape (adding/removing fields, changing defaults) will load stale data from localStorage and cause unpredictable behavior.

```tsx
// ❌ WRONG — no version, no migration
persist(
    (set) => ({ fontKey: "system", scaleKey: "m", ... }),
    { name: "app-settings" }
)

// ✅ CORRECT — versioned with reset migration
persist(
    (set) => ({ fontKey: "system", scaleKey: "m", ... }),
    {
        name: "app-settings",
        version: 1,
        migrate: () => ({
            fontKey: "system", scaleKey: "m",
            setFont: () => {}, setScale: () => {},
        }),
    }
)
```

**Bump the version** whenever you change defaults or add/remove fields. The `migrate` function runs automatically when the stored version doesn't match, resetting to clean defaults.

### Gotcha 3 — CSS Token Contrast Hierarchy (3-Tier Rule)

The bridge mapping must maintain a **3-tier contrast hierarchy** for text tokens. This is critical for themes with low-contrast accent colors (Matrix, One Dark, Monokai).

```
text        → --text-1  (highest contrast — headings, primary content)
text-secondary → --text-2  (medium contrast — labels, descriptions)
text-muted     → --text-3  (lowest contrast — hints, inactive states)
```

> [!WARNING]
> **Common Mistake:** Mapping `--color-text-muted` to `--text-muted` (the raw theme variable). In many themes, `--text-muted` has extremely low opacity (e.g., `rgba(16, 185, 129, 0.4)` in Matrix), making muted text nearly invisible. Always map to `--text-3` instead.

**Interactive Element Rule:** Buttons, toggles, and clickable elements should use `text-secondary` (not `text-muted`) as their resting color. This ensures they remain visible across all 9 themes while still maintaining hierarchy below primary text.

### Gotcha 4 — Bridge Mapping Verification Checklist

After modifying themes or bridge mappings, verify contrast with this checklist:

```
For each theme, verify in browser DevTools:
  □ text vs text-secondary → visually distinct (not the same shade)
  □ text-secondary vs text-muted → visually distinct (clear hierarchy)
  □ text-muted → still readable (not invisible against bg-root)
  □ Interactive elements (buttons, toggles) use text-secondary, not text-muted
  □ Labels/captions use text-muted (lowest tier — appropriate for non-interactive)
  □ Settings button, sidebar collapse button → clearly visible in all themes
```

> Themes most likely to expose contrast bugs: **Matrix** (green on black), **One Dark** (muted blues), **VS Code** (neutral grays).

