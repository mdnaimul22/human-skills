<div align="center">

<img src="assets/banner.svg" alt="Human Skills — Cyberpunk Banner" width="100%"/>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
![Skills: Verified](https://img.shields.io/badge/Skills-Human--Verified-00FF41?style=flat-square&labelColor=0d0d0d)

</div>

---

## What is Human Skills?

A curated, **human-verified** collection of AI coding skills. Every skill in this repository has been tested on real tasks with consistent, reliable results — no blind prompts, no untested instructions.

This repo also ships **executable tools** — registered CLI utilities (linter, bootstrap, tree generator, etc.) that can be invoked from anywhere via the `human-skills` dispatcher.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/mdnaimul22/human-skills.git
cd human-skills

# Install the global CLI dispatcher
chmod +x scripts/install.sh
./scripts/install.sh
```

This binds the `human-skills` command to `~/.local/bin`, making all tools accessible from any directory.

### Usage

```bash
# List all available skills & tools
human-skills --list

# Read a skill's documentation
human-skills --skill_info architecture-auditing-linter

# Inspect a specific tool's schema
human-skills --tool_info linter

# Run a tool
human-skills '{
    "tool_name": "linter",
    "tool_args": {
        "scan_path": "/path/to/your/project",
        "ignored_path": "venv, .git, tests"
    }
}'
```

---

## Bootstrap New Project

To scaffold a new Python project with the standard directory structure, config layer, and agent rules:

```bash
curl -sSL https://raw.githubusercontent.com/mdnaimul22/human-skills/main/skills/python-project-setup/resources/initialize/bootstrap.py | python3
```

This creates:

```
new-project/
├── src/
│   ├── config/      # Settings, paths, dotenv, files utilities
│   ├── core/        # Business logic
│   ├── helpers/     # Global utilities (logger, exceptions)
│   ├── providers/   # External service integrations
│   ├── schema/      # Pydantic models
│   ├── services/    # Use-case orchestration
│   └── routers/     # HTTP interface
├── tests/
├── docs/
├── .agents/rules/   # Coding standards synced from this repo
├── main.py
├── .env
└── .gitignore
```

---

## Sync Agent Rules

To sync only the `.agents/rules/` folder into an existing project:

```bash
curl -sSL https://raw.githubusercontent.com/mdnaimul22/human-skills/main/scripts/sync-rules.sh | bash
```

---

## What Makes a Skill "Human-Verified"?

A skill qualifies for this repo when:

- [x] You have used it in a **real task** (not just read it)
- [x] The AI followed its instructions and **produced correct output**
- [x] You ran it **more than once** with consistent results
- [x] You are confident recommending it to others

Blind skills — instruction files that look good on paper but have never been tested — are explicitly excluded.

---

## Repository Structure

```
human-skills/
├── skills/                          # ✅ Human-verified skills & tools
│   ├── architecture-auditing-linter/  # AST-based code auditor
│   ├── python-project-setup/          # Bootstrap + config scaffolding
│   ├── directory-structure/           # Tree generator tool
│   ├── helpers/                       # Dispatcher runtime
│   ├── coding-standareds/             # Always-on coding rules
│   ├── project-tree-example/          # Canonical project structures
│   ├── ui-ux-pro-max/                 # Design system (161 palettes, 57 fonts)
│   ├── docx/ pdf/ pptx/ xlsx/         # Document generation skills
│   └── ...
│
├── .agents/rules/                   # 📐 Coding standards & architecture rules
│
├── scripts/
│   ├── install.sh                   # Global CLI installer
│   └── sync-rules.sh               # Agent rules syncer
│
└── assets/
```

---

## Contributing

If you want to contribute a skill:

1. Run the skill on a real task
2. Verify the output is correct
3. Run it again to confirm consistency
4. Submit a PR with the skill folder and a brief note on what you tested

Skills submitted without evidence of testing will not be merged.

---

## License

MIT — see [LICENSE](LICENSE).
