<div align="center">

```
██╗  ██╗██╗   ██╗███╗   ███╗ █████╗ ███╗   ██╗    ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗
██║  ██║██║   ██║████╗ ████║██╔══██╗████╗  ██║    ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝
███████║██║   ██║██╔████╔██║███████║██╔██╗ ██║    ███████╗█████╔╝ ██║██║     ██║     ███████╗
██╔══██║██║   ██║██║╚██╔╝██║██╔══██║██║╚██╗██║    ╚════██║██╔═██╗ ██║██║     ██║     ╚════██║
██║  ██║╚██████╔╝██║ ╚═╝ ██║██║  ██║██║ ╚████║    ███████║██║  ██╗██║███████╗███████╗███████║
╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝
```

### 🔬 If it hasn't been tested by a human, it doesn't belong here.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Skills: Verified](https://img.shields.io/badge/Skills-Human--Verified-brightgreen)
![Sync: Automated](https://img.shields.io/badge/Sync-Automated-blue)
![Hot Reload: ON](https://img.shields.io/badge/Hot--Reload-ON-blueviolet)

</div>

---

## What is Human Skills?

The internet is full of AI skill repositories — thousands of instruction files telling AI assistants *how* to behave for specific tasks. The problem? Most of them are **blind skills**: written once, never run, never verified.

**Human Skills** is different.

A skill earns its place in this repository only after it has been:

1. **Run multiple times** against a real task
2. **Verified by a human** to produce correct, useful output
3. **Proven consistent** — not a one-off lucky result

If a skill has never been tested end-to-end by a human, it has **no place here**.

---

## Who is this for?

| User | How they benefit |
|---|---|
| **You (the admin)** | A personal, curated knowledge base — no more drowning in unverified skill repos |
| **Anyone who clones this** | A ready-to-use, tested skill library they can drop into their own AI setup |
| **Teams** | A shared standard for what "a working skill" actually means |

---

## Repository Structure

```
human-skills/
├── skills/                         # ✅ Human-verified skills live here
│   ├── directory-structure/
│   ├── manage_project/
│   ├── openevolve-evolutionary-coding/
│   ├── zram-optimizer/
│   └── ...
│
├── scripts/
│   ├── sync.py                     # Automated upstream sync daemon
│   ├── requirements.txt
│   └── helpers/
│       ├── upstream.yaml           # Which repos to pull from daily
│       ├── path_forward.yaml       # Which skills to copy into skills/
│       └── automation.yaml         # Schedule, git, and logging settings
│
├── .claude-skills/                 # Upstream repos (git submodules / clones)
├── .everything-claude-code/
└── .superpowers/
```

---

## Core Concept: Upstream Tracking + Skill Forwarding

Many great skill repos exist in the open-source community. Instead of copying them manually or losing track of updates, Human Skills uses a **two-step pipeline**:

```
Upstream repo (someone else's skills)
    ↓  git pull (daily, automated)
Local upstream clone
    ↓  copy only the verified skill folders
skills/  ← your curated, human-verified collection
    ↓  git commit + push (automatic)
Your GitHub repo (always up to date)
```

You stay in control of **what gets promoted** into `skills/`. Everything else in the upstream stays there — you only forward what you've verified works.

---

## Quick Start: Use This Repo As-Is

```bash
# Clone the repo
git clone https://github.com/mdnaimul22/human-skills.git
cd human-skills

# Install sync script dependencies
pip install -r scripts/requirements.txt
```

Point your AI assistant's skill loader at the `skills/` directory. Every folder inside contains a `SKILL.md` that has been human-verified to work.

---

## Personalising for Your Own Setup

### Step 1 — Fork the repo

Fork this repo on GitHub so you have your own copy to push to.

### Step 2 — Configure git identity

```bash
git config user.name  "Your Name"
git config user.email "your@email.com"
```

### Step 3 — Add your upstream repos

Edit `scripts/helpers/upstream.yaml`:

```yaml
upstreams:

  - name: some-skill-repo
    path: /absolute/path/to/cloned/some-skill-repo

  - name: another-repo
    path: /absolute/path/to/cloned/another-repo
```

Each entry is a locally cloned git repository. The sync script will run `git pull` in each one every day.

### Step 4 — Define which skills to forward

Edit `scripts/helpers/path_forward.yaml`:

```yaml
forwards:

  - from: /absolute/path/to/cloned/some-skill-repo/skills/skill-name
    to:   /absolute/path/to/human-skills/skills/skill-name
    enabled: true

  - from: /absolute/path/to/cloned/another-repo/skills/other-skill
    to:   /absolute/path/to/human-skills/skills/other-skill
    enabled: true

  # Temporarily pause a forward without deleting it:
  - from: /absolute/path/to/cloned/some-skill-repo/skills/unverified-skill
    to:   /absolute/path/to/human-skills/skills/unverified-skill
    enabled: false
```

> **Rule of thumb:** Only set `enabled: true` for skills you have personally run and verified. This is what makes it a *Human Skill*.

### Step 5 — Tune the schedule

Edit `scripts/helpers/automation.yaml`:

```yaml
schedule:
  run_at: "06:00"            # Daily at 6 AM — change to your preference
  interval_hours: 24         # Used if run_at is null
  poll_interval_seconds: 30  # How often to check for config file changes

git:
  auto_push: true
  branch: main
  commit_message: "sync: auto-update from upstream [{datetime}]"

logging:
  level: INFO
  log_file: /absolute/path/to/human-skills/scripts/logs/sync.log
```

---

## Running the Sync Daemon

The sync script is designed to run **persistently inside a `screen` session** so it survives terminal closure.

```bash
# Start a named screen session
screen -S human-skills-sync

# Run the daemon
python3 /path/to/human-skills/scripts/sync.py

# Detach from screen (daemon keeps running in background)
# Press:  Ctrl+A, then D

# Reconnect at any time to check logs
screen -r human-skills-sync
```

On every sync cycle the daemon:

1. **Pulls** all upstream repos (`git pull`)
2. **Copies** the forwarded skill folders into `skills/`
3. **Commits** all changes with a timestamped message
4. **Pushes** to your remote repository automatically

---

## Hot-Reload — No Restart Needed

The daemon watches `scripts/helpers/*.yaml` for file changes every `poll_interval_seconds`. If you edit any config file while the script is running:

| What you change | What happens automatically |
|---|---|
| Add a new upstream in `upstream.yaml` | Picked up on next sync cycle |
| Add a new forward in `path_forward.yaml` | Picked up on next sync cycle |
| Set `enabled: false` on a forward | Skipped from next sync onwards |
| Change `run_at` in `automation.yaml` | Schedule cleared and re-registered immediately |
| Change `poll_interval_seconds` | New interval takes effect on next loop tick |

You never need to restart the script.

---

## What Makes a Skill "Human-Verified"?

A skill qualifies for this repo when:

- [x] You have used it in a **real task** (not just read it)
- [x] The AI followed its instructions and **produced correct output**
- [x] You ran it **more than once** with consistent results
- [x] You are confident recommending it to others

Blind skills — instruction files that look good on paper but have never been tested — are explicitly excluded.

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