---
name: scaffold-ui
description: Scaffolds a complete Next.js + shadcn/ui + Tailwind CSS frontend with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client.
---

# Scaffold UI
> *"One command. Full frontend."*

Scaffolds a complete **Next.js + shadcn/ui + Tailwind CSS** frontend layer (`web/`) with 9 built-in themes, layout components, OAuth auth pages, and a secure FastAPI API client.

## How to Use

```bash
human-skills '{
    "tool_name": "setui",
    "tool_args": {
        "destination": "/path/to/your_project"
    }
}'
```

---

## What SetUI Creates

```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx              ← Root layout + ThemeProvider (anti-flicker)
│   │   ├── globals.css             ← 9 themes + design tokens + shadcn vars
│   │   ├── (auth)/                 ← Auth pages (no sidebar/navbar)
│   │   │   ├── layout.tsx          ← Centered card layout
│   │   │   └── login/page.tsx      ← OAuth + email/password form
│   │   └── (dashboard)/            ← Dashboard pages (with sidebar/navbar)
│   │       ├── layout.tsx          ← Sidebar + Navbar wrapper
│   │       └── page.tsx            ← Dashboard home (placeholder)
│   │
│   ├── components/
│   │   ├── ui/                     ← shadcn components (30+ auto-installed)
│   │   ├── layout/
│   │   │   ├── app-shell.tsx       ← Root layout wrapper
│   │   │   ├── sidebar.tsx         ← Collapsible sidebar (280px ↔ 64px)
│   │   │   ├── navbar.tsx          ← Top bar (search, notifications, avatar)
│   │   │   ├── page-header.tsx     ← Page title + action buttons
│   │   │   └── theme-switcher.tsx  ← Theme dropdown (9 themes)
│   │   └── auth/
│   │       └── login-form.tsx      ← Google + GitHub OAuth buttons
│   │
│   ├── lib/
│   │   ├── api.ts                  ← Secure FastAPI client (timeout, typed errors)
│   │   └── utils.ts                ← cn() utility (clsx + tailwind-merge)
│   │
│   ├── hooks/
│   │   └── use-sidebar.ts          ← Sidebar state (Zustand, persisted)
│   │
│   └── types/
│       └── api.ts                  ← Auto-generated from FastAPI (placeholder)
│
├── scripts/
│   └── generate-types.sh           ← OpenAPI → TypeScript auto-gen
│
├── components.json                 ← shadcn config
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
└── package.json
```

---

## Theme System

9 themes are included (7 dark + 2 light):

| Theme | Accent | Type |
|:---|:---|:---|
| Default Dark | `#3b82f6` (Blue) | 🌙 Dark |
| Matrix | `#10b981` (Green) | 🌙 Dark |
| Monokai | `#a6e22e` (Lime) | 🌙 Dark |
| VS Code | `#007acc` (Blue) | 🌙 Dark |
| Dracula | `#bd93f9` (Purple) | 🌙 Dark |
| One Dark | `#61afef` (Blue) | 🌙 Dark |
| Nord | `#88c0d0` (Cyan) | 🌙 Dark |
| Clear Ice | `#1d4ed8` (Deep Blue) | ☀️ Light |
| Snow | `#3b82f6` (Blue) | ☀️ Light |

### Three-Layer Token Architecture

```
Theme Definition (raw)    →  --accent: #10b981
         ↓
Bridge Mapping (auto)     →  --color-primary: var(--accent)
         ↓
shadcn/ui Mapping (auto)  →  --primary: var(--color-primary)
```

**Adding a new theme** = define ~25 CSS variables. The bridge + shadcn mapping auto-handles everything.

---

## Anti-Flicker Strategy

Theme switching is flicker-free:
1. `next-themes` reads theme from `localStorage` **before first paint** via inline `<script>`
2. `suppressHydrationWarning` on `<html>` prevents React hydration mismatch
3. Background transitions disabled on first load, enabled after mount via `body.theme-loaded`
4. `enableSystem={false}` — no OS detection race condition

## Security

- **API Client:** Request timeout (15s), `credentials: "include"` for httpOnly cookies
- **Auth:** OAuth via server-side redirects (not client-side token storage)
- **No localStorage tokens** — auth tokens live in httpOnly cookies only
- **XSS Protection:** No `innerHTML` or `eval()` — JSON.parse only

---

## Post-Scaffolding

1. `cd web && npm install && npm run dev` → Open http://localhost:3000
2. Add `NEXT_PUBLIC_API_URL=http://localhost:8000` to `web/.env.local`
3. Generate types: `bash web/scripts/generate-types.sh`
4. Edit `NAV_ITEMS` in `sidebar.tsx` to add navigation links
5. Add new pages under `app/(dashboard)/`
