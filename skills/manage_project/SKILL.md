---
name: "project-manager"
description: "Manage AI agent projects: create, configure, update, delete, and add instructions/knowledge. Use this tool to perform project lifecycle operations."
author: "Human Skill Team"
tags: ["project", "management", "configuration", "git", "setup"]
trigger_patterns:
  - "create project"
  - "new project"
  - "creat a project"
  - "create a project"
  - "a new project"
  - "creat project"
  - "project setup"
  - "project manage"
  - "manage project"
  - "project manager"
  - "configure project"
  - "update project"
  - "delete project"
  - "add project rules"
  - "clone project"
  - "project status"
---

## Overview

This skill provides complete guidance for setting up unified AI projects, including:
- Project creation (empty or Git-based)
- Custom instructions and configuration
- Memory management (isolated or shared)
- Knowledge base integration
- Agent configuration
- Secrets and variables management

### 1. Project Creation
- Create empty projects from scratch
- Clone Git repositories directly into projects
- Automatic configuration merging for existing `a0/usr/projects/my-project/.a0proj/` folders

### 2. Instructions System
- Main instructions field in project configuration
- Additional instruction files in `a0/usr/projects/my-project/.a0proj/instructions/`
- Automatic concatenation and injection into agent context

### 3. Memory Management
- **Own memory**: Isolated vector database per project
- **Global memory**: Shared memory pool across related projects

### 4. Knowledge Base
- Custom knowledge files in `a0/usr/projects/my-project/.a0proj/knowledge/main/`
- Automatic documentation indexing from `a0/usr/projects/my-project/docs/`
- Support for PDF, text, CSV, HTML, JSON, and Markdown

### 5. Agent Configuration
- Project-specific subagent profiles
- Custom system prompts per profile
- Model and temperature settings

### 6. Security
- Project-scoped secrets in `a0/usr/projects/my-project/.a0proj/secrets.env`
- Non-sensitive variables in `a0/usr/projects/my-project/.a0proj/variables.env`
- Automatic Git exclusion for secrets

## manage_project tool
The `manage_project` tool allows you to programmatically manage the entire lifecycle of unified AI projects.

**Supported Actions:**
- **Lifecycle:** `create`, `list`, `load`, `delete`
- **Git:** `clone`, `git_status`
- **Config:** `update`, `set_variables`
- **Content:** `add_rules`, `add_knowledge`

---

## Decision Tree

1. **New Project?**
   - From scratch? -> Use `create`
   - From existing repo? -> Use `clone`

2. **Setup Rules?**
   - Apply coding standards/workflows? -> Use `add_rules` (e.g., `rules="python-coding-style.md, common-git-workflow.md"`)

3. **Modify Project?**
   - Change settings? -> Use `update`
   - Add reference docs? -> Use `add_knowledge`
   - Set ENV vars? -> Use `set_variables`

---

## workflow examples-1

**Action:** `clone`
**Required:** `project_name` (lowercase, no spaces), `git_url`

#### 1 cloning git url by manage_project tool
```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "clone",
        "project_name": "simple-dantd",
        "git_url": "https://github.com/mdnaimul22/simple-dantd",
    }
}
```
#### 1.1 generatating dependancy graph structure fpr the project
Use this tree structure generator tool to understand project structure before adding guidelines, instructions, coding standards, workflows.

**Example:**
```json
{
    "thoughts": [
        "Generating structure for project my-project"
    ],
    "tool_name": "tree_gen",
    "tool_args": {
        "tree_structure_input_path": "/a0/usr/my-project/",
        "tree_structure_out_path": "/a0/usr/my-project/",
        "ignored_path": "node_modules, dist, build, tests, __tests__, coverage, .git, .vscode, public/images"
    }
}
```
this tool will generate a project /a0/usr/workdir/my-project/structure.md thats give you undrestand the full view of the project. and after reading structure.md you can decide which docs and readme you have to read for generating well project 01_instruction.md
note: this 01_instruction.md is prompt instruction and you have to read README.md or under project docs to undrestand how well you can generate a prompt instruction. also remember this tool command work only when a git repo already avoilable. 

#### 1.2 Code Viewing Tools

**view_file** - Use this tool to view the entire content of a file.

This tool is simple and powerful. Just provide the absolute path to the file you want to see.

```json
{
    "thoughts": [
        "I need to examine the structure.md to undrestand full graph and file location"
    ],
    "Headline": "Reviewing structure.md file for details analysis",
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path": "/a0/usr/my-project/structure.md"
    }
}
```
#### 1.3 Code Viewing Tools
```json
{
    "thoughts": [
        "I found README.md so i need to examine the file content"
    ],
    "Headline": "Reviewing README.md file for details analysis",
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path": "/a0/usr/my-project/README.md"
    }
}
```
#### 1.4 Code Viewing Tools
```json
{
    "thoughts": [
        "lets examine more docs to undrestand the repository context from /docs"
    ],
    "Headline": "Reviewing reach documenation file for details analysis",
    "tool_name": "view_file",
    "tool_args": {
        "absolute_path": "/a0/usr/my-project/docs/docname*"
    }
}
```

#### 2.0 using manage_project tool again for better title, description, prompt instruction
after analysis README and some of core documentation you know this project well. so update now title, description, instructions following below pattern
```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "update",
        "project_name": "finance-bot",
        "title": "Finance Automation Bot",
        "description": "Automates daily financial reports",
        "instructions": "## Role\nYou are a financial analyst...",
        "color": "#10B981"
    }
}
```

### 3.0 Add Rules (Templates)
all avoilable rules set already stored inside this skill a0/usr/skills/project-setup/templates
use manage project tool to transfer project related rules. such as if a project built on python then its need python related rule Templates, or if a project built on typescript where if you send js related rule then it create confusion. so always transfer right rule templets.

**Action:** `add_rules`
**Purpose:** Copy pre-defined rule templates to project instructions.
**Templates Location:** `a0/usr/skills/project-setup/templates`

**common templates:**
- `common-coding-style.md`
- `common-git-workflow.md`
- `common-patterns.md`
- `common-security.md`
- `common-testing.md`

**context templates:**
- `context-dev.md`
- `context-research.md`
- `context-review.md`

**python templates:**
- `python-coding-style.md`
- `python-hooks.md`
- `python-patterns.md`
- `python-security.md`
- `python-testing.md`

```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "add_rules",
        "project_name": "simple-dantd",
        "rules": "python-coding-style.md, common-git-workflow.md"
    }
}
```

### 4.0 Add Knowledge
When our system support Automatic documentation indexing from `a0/usr/projects/my-project/docs/` here some times you see some of git repo has no docs, So building Custom knowledge base by analysis project code and structure are most essential.Support for PDF, text, CSV, HTML, JSON, and Markdown. When you add tool_args filename and content it will be Stored as Custom knowledge files in `a0/usr/projects/my-project/.a0proj/knowledge/main/`

**Action:** `add_knowledge`
**Purpose:** Add reference documents to `.a0proj/knowledge/main/`

```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "add_knowledge",
        "project_name": "simple-dantd",
        "filename": "api-docs.md",
        "content": "# API Documentation\n..."
    }
}
```

### 5. Set Variables

**Action:** `set_variables`
**Purpose:** Set environment variables (non-sensitive)

```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "set_variables",
        "project_name": "simple-dantd",
        "variables": "API_URL=https://api.example.com\nDEBUG=true"
    }
}
```

### 6. Get Git Status

**Action:** `git_status`

```json
{
    "tool_name": "manage_project",
    "tool_args": {
        "action": "git_status",
        "project_name": "simple-dantd"
    }
}
```

### 7. List & Load

```json
// List all
{ "tool_name": "manage_project", "tool_args": { "action": "list" } }

// Load one
{ "tool_name": "manage_project", "tool_args": { "action": "load", "project_name": "finance-bot" } }
```

---

## Best Practices

### ✅ DO:
1. **Use `clone` for existing repos** instead of `create`.
2. **Use `add_rules`** to apply standard templates instead of writing raw instructions.
3. **Use lowercase `project_name`**, e.g., `my-project`.

### ❌ DON'T:
1. **Don't put secrets in `set_variables`**.
2. **Don't use spaces in `project_name`**.
