---
name: "a0-manage-project"
description: "Manage Agent Zero projects: create, configure, update, delete, and add instructions/knowledge. Use this tool to perform project lifecycle operations."
author: "Agent Zero Team"
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
  - "a0 manage project"
  - "configure project"
  - "update project"
  - "delete project"
  - "add project rules"
  - "clone project"
  - "project status"
---

## Overview

This skill provides complete guidance for setting up Agent Zero projects, including:
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

## a0_manage_project tool
The `a0_manage_project` tool allows you to programmatically manage the entire lifecycle of Agent Zero projects.

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

## Workflow Examples

**Action:** `clone`  
**Required:** `project_name` (lowercase, no spaces), `git_url`

#### 1. Cloning Git URL by a0_manage_project Tool
```json
{
    "tool_name": "a0_manage_project",
    "tool_args": {
        "action": "clone",
        "project_name": "simple-dantd",
        "git_url": "https://github.com/mdnaimul22/simple-dantd"
    }
}
```

#### 2. Update Project Metadata & Instructions
```json
{
    "tool_name": "a0_manage_project",
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

#### 3. Add Rule Templates
```json
{
    "tool_name": "a0_manage_project",
    "tool_args": {
        "action": "add_rules",
        "project_name": "simple-dantd",
        "rules": "python-coding-style.md, common-git-workflow.md"
    }
}
```

#### 4. Add Knowledge File
```json
{
    "tool_name": "a0_manage_project",
    "tool_args": {
        "action": "add_knowledge",
        "project_name": "simple-dantd",
        "filename": "api-docs.md",
        "content": "# API Documentation\n..."
    }
}
```

#### 5. Set Environment Variables
```json
{
    "tool_name": "a0_manage_project",
    "tool_args": {
        "action": "set_variables",
        "project_name": "simple-dantd",
        "variables": "API_URL=https://api.example.com\nDEBUG=true"
    }
}
```

#### 6. Check Git Status
```json
{
    "tool_name": "a0_manage_project",
    "tool_args": {
        "action": "git_status",
        "project_name": "simple-dantd"
    }
}
```

#### 7. List & Load Projects
```json
// List all projects
{ "tool_name": "a0_manage_project", "tool_args": { "action": "list" } }

// Load specific project
{ "tool_name": "a0_manage_project", "tool_args": { "action": "load", "project_name": "finance-bot" } }
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
