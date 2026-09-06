---
trigger: always_on
name: git_workflow
description: "Git commit message format, branch conventions, PR workflow, and safety standards"
---

# Git Workflow & Standards

## 1. Safety & Permissions (CRITICAL)

- **Secrets Protection:** NEVER stage or commit `.env`, `secrets.env`, credentials, private tokens, or temporary cache files. Always verify `.gitignore`.
- **User Confirmation:** Always confirm with the user before creating commits or pushing branches.
- **Pre-commit Check:** Run `git status` and `git diff` to ensure only intended files are staged.

---

## 2. Conventional Commit Format

Use clear, standardized commit messages:

```
<type>(<optional scope>): <short imperative description>

<optional detailed body explaining why and what changed>
```

### Commit Types:
- `feat`: A new feature or capability
- `fix`: A bug fix
- `refactor`: Code changes that neither fix a bug nor add a feature
- `docs`: Documentation changes only
- `test`: Adding or correcting tests
- `chore`: Build tasks, dependencies, or configuration updates
- `perf`: Performance improvements

---

## 3. Branching & Feature Workflow

1. **Branch Creation:**
   - Use clean, descriptive branch names: `feat/<feature-name>`, `fix/<issue-name>`, `refactor/<module>`.
2. **Atomic Commits:**
   - Keep commits small, logical, and focused on a single responsibility.
3. **Verification Before Commit:**
   - Ensure local tests pass and linters report no critical errors before committing.
4. **Pull Requests (PR):**
   - Review changes with `git diff [base-branch]...HEAD`.
   - Provide a clear PR summary with changes made, testing steps, and verification results.

