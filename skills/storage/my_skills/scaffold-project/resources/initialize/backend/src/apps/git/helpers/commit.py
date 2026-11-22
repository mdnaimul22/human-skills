from __future__ import annotations
from src.config import Settings, setup_logger
from src.apps.git.providers import get_status, run_git
from src.apps.git.schema import CommitMessages, ForwardRule, UpstreamEntry
from .classifier import ChangeClassifier

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.commit")


class CommitEngine:
    def __init__(self, repo_root: str) -> None:
        self.repo_root = repo_root

    def _current_branch(self) -> str | None:
        res = run_git(["rev-parse", "--abbrev-ref", "HEAD"], self.repo_root)
        if not res.ok:
            return None
        branch = res.output.strip()
        if not branch or branch == "HEAD":
            return None
        return branch

    def _resolve_push_branch(self, configured_branch: str) -> str | None:
        current = self._current_branch()
        if current is None:
            logger.error("Cannot resolve current git branch (detached HEAD or git error)")
            return None
        raw = configured_branch.strip()
        if raw.lower() in ("", "head", "auto", "current"):
            return current
        if raw != current:
            logger.error(
                f"Branch mismatch: HEAD is '{current}' but configured push branch is '{raw}'. Set branch to '{current}' or 'HEAD'."
            )
            return None
        return raw

    def _push_branch(self, target_branch: str, label: str) -> bool:
        push = run_git(["push", "origin", target_branch], self.repo_root)
        if not push.ok:
            logger.error(f"Push of {label} to origin/{target_branch} failed: {push.output}")
            return False
        logger.info(f"Pushed {label} to origin/{target_branch}")
        return True

    def classify_managed(
        self, status_output: str, forwards: list[ForwardRule], upstreams: list[UpstreamEntry],
    ) -> dict[str, list[str]]:
        classifier = ChangeClassifier(forwards, upstreams, repo_root=self.repo_root)
        return classifier.classify_managed(status_output)

    def commit_orphans(
        self, removed_paths: list[str], branch: str, current_time: str,
        auto_push: bool, auto_commit: bool = True,
    ) -> bool:
        if not removed_paths or not auto_commit:
            return True
        target_branch = self._resolve_push_branch(branch) if auto_push else None
        if auto_push and target_branch is None:
            return False
        msg = f"chore: remove {len(removed_paths)} orphaned managed path(s) [{current_time}]"
        cmt = run_git(["commit", "--only", "-m", msg, "--", *removed_paths], self.repo_root)
        if not cmt.ok:
            if "nothing to commit" in cmt.output:
                return True
            logger.warning(f"Orphan commit failed: {cmt.output}")
            return False
        if not auto_push or target_branch is None:
            return True
        return self._push_branch(target_branch, "orphan cleanup")

    def commit_and_push(
        self, upstream_changes: dict[str, list[str]], branch: str, current_time: str,
        commit_messages: CommitMessages, auto_push: bool, auto_commit: bool = True,
    ) -> tuple[bool, list[str]]:
        if not auto_commit or not any(files for files in upstream_changes.values()):
            return True, []
        target_branch = self._resolve_push_branch(branch) if auto_push else None
        if auto_push and target_branch is None:
            return False, []

        committed_upstreams: list[str] = []
        for up_name, files in upstream_changes.items():
            if not files:
                continue
            if self._commit_upstream_batch(up_name, files, current_time, commit_messages):
                committed_upstreams.append(up_name)

        if not committed_upstreams or not auto_push or target_branch is None:
            return True, committed_upstreams
        return self._push_branch(target_branch, f"{len(committed_upstreams)} upstream batch(es)"), committed_upstreams

    def _commit_upstream_batch(
        self,
        up_name: str,
        files: list[str],
        current_time: str,
        commit_messages: CommitMessages,
    ) -> bool:
        status_res = get_status(self.repo_root)
        status_out = status_res.output if status_res.ok else ""
        files_to_add = ChangeClassifier.filter_staged_deletions(files, status_out)
        if files_to_add:
            add_res = run_git(["add", "--", *files_to_add], self.repo_root)
            if not add_res.ok:
                logger.error(f"git add failed for {up_name}: {add_res.output}")
                return False

        template = commit_messages.upstreams.get(
            up_name,
            commit_messages.upstreams.get("default", "sync: auto-update from {upstream_name} [{datetime}]"),
        )
        msg = (
            template
            .replace("{upstream_name}", up_name)
            .replace("{count}", str(len(files)))
            .replace("{datetime}", current_time)
        )
        cmt = run_git(["commit", "--only", "-m", msg, "--", *files], self.repo_root)
        if cmt.ok:
            logger.info(f"Committed {len(files)} managed file(s) for [{up_name}]")
            return True
        if "nothing to commit" not in cmt.output:
            logger.warning(f"Commit warning for [{up_name}]: {cmt.output}")
        return False
