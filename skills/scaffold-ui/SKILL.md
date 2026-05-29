---
name: scaffold-ui
description: Scaffolds a complete Next.js + shadcn/ui + Tailwind CSS frontend with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client. Bridges with ui-ux-pro-max for AI-powered custom themes.
---

# Scaffold UI
> *"One command. Full frontend. Intelligent theming."*

Scaffolds a complete **Next.js + shadcn/ui + Tailwind CSS** frontend layer (`web/`) with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client.

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
