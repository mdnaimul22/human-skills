from __future__ import annotations
from src.config import Settings, ensure_dir, exists, get_abs_path, get_rel_path, setup_logger
from src.apps.git.providers import run_git
from src.apps.git.schema import ForwardRule, UpstreamEntry

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.upstream")


class UpstreamResolver:
    @staticmethod
    def resolve_sparse_subpaths(entry: UpstreamEntry, forwards: list[ForwardRule], repo_root: str = "") -> list[str]:
        if not forwards:
            return []
        up_path = get_rel_path(entry.path, repo_root).rstrip("/")
        subpaths: set[str] = set()
        for rule in forwards:
            if not rule.enabled or not rule.from_path:
                continue
            from_p = get_rel_path(rule.from_path, repo_root).rstrip("/")
            if from_p == up_path:
                return []
            rel_sub = UpstreamResolver._extract_subpath(entry, rule, up_path, from_p)
            if rel_sub:
                subpaths.add(rel_sub)
        return sorted(subpaths)

    @staticmethod
    def _extract_subpath(entry: UpstreamEntry, rule: ForwardRule, up_path: str, from_p: str) -> str:
        if from_p.startswith(f"{up_path}/"):
            return from_p[len(up_path):].strip("/")
        if rule.upstream_id and entry.upstream_id and rule.upstream_id == entry.upstream_id:
            if from_p.startswith(up_path):
                return from_p[len(up_path):].strip("/")
            return from_p.strip("/")
        return ""


class UpstreamEngine:
    def __init__(self, repo_root: str = "") -> None:
        self.repo_root = repo_root

    def _resolve_target(self, entry_path: str) -> str:
        if self.repo_root and not entry_path.startswith("/"):
            return get_abs_path(self.repo_root, entry_path)
        return get_abs_path(entry_path)

    def _clone_sparse(self, entry: UpstreamEntry, target_path: str, parent: str, sparse_subpaths: list[str]) -> bool:
        clone_cmd = ["clone", "-b", entry.branch]
        if entry.blobless:
            clone_cmd.append("--filter=blob:none")
        clone_cmd.extend(["--no-checkout", entry.url, target_path])
        res = run_git(clone_cmd, parent)
        if not res.ok:
            logger.warning(f"[{entry.project_name}] Optimized clone failed ({res.output}), retrying standard clone")
            return run_git(["clone", "-b", entry.branch, entry.url, target_path], parent).ok
        run_git(["sparse-checkout", "init", "--cone"], target_path)
        run_git(["sparse-checkout", "set", "--skip-checks", *sparse_subpaths], target_path)
        checkout_res = run_git(["checkout", entry.branch], target_path)
        if not checkout_res.ok:
            logger.warning(f"[{entry.project_name}] Sparse checkout retry: {checkout_res.output}")
            return run_git(["checkout", entry.branch], target_path).ok
        return True

    def _clone_full(self, entry: UpstreamEntry, target_path: str, parent: str) -> bool:
        clone_cmd = ["clone", "-b", entry.branch]
        if entry.blobless:
            clone_cmd.append("--filter=blob:none")
        clone_cmd.extend([entry.url, target_path])
        res = run_git(clone_cmd, parent)
        if not res.ok and entry.blobless:
            logger.warning(f"[{entry.project_name}] Blobless clone failed ({res.output}), retrying standard clone")
            return run_git(["clone", "-b", entry.branch, entry.url, target_path], parent).ok
        return res.ok

    def _pull_existing(self, entry: UpstreamEntry, target_path: str, sparse_subpaths: list[str]) -> tuple[bool, bool]:
        old_head = run_git(["rev-parse", "HEAD"], target_path).output
        if sparse_subpaths:
            run_git(["sparse-checkout", "set", "--skip-checks", *sparse_subpaths], target_path)
        fetch_cmd = ["fetch", "origin", entry.branch]
        if entry.blobless:
            fetch_cmd.append("--filter=blob:none")
        fetch_res = run_git(fetch_cmd, target_path)
        if not fetch_res.ok:
            logger.error(f"[{entry.project_name}] Fetch failed: {fetch_res.output}")
            return False, False
        reset_res = run_git(["reset", "--hard", f"origin/{entry.branch}"], target_path)
        if not reset_res.ok:
            logger.error(f"[{entry.project_name}] Reset failed: {reset_res.output}")
            return False, False
        new_head = run_git(["rev-parse", "HEAD"], target_path).output
        return True, (old_head != new_head or bool(sparse_subpaths))

    def pull(self, upstreams: list[UpstreamEntry], forwards: list[ForwardRule]) -> tuple[dict[str, bool], list[str]]:
        results: dict[str, bool] = {}
        updated: list[str] = []
        for entry in upstreams:
            if not entry.pull:
                results[entry.project_name] = True
                continue
            target_path = self._resolve_target(entry.path)
            sparse_subpaths = (
                UpstreamResolver.resolve_sparse_subpaths(entry, forwards, repo_root=self.repo_root)
                if entry.sparse
                else []
            )
            if not exists(target_path):
                if not entry.url:
                    logger.warning(f"[{entry.project_name}] Path missing and no URL configured: {target_path}")
                    results[entry.project_name] = False
                    continue
                parent = target_path.rsplit("/", 1)[0]
                ensure_dir(parent)
                ok = (
                    self._clone_sparse(entry, target_path, parent, sparse_subpaths)
                    if sparse_subpaths
                    else self._clone_full(entry, target_path, parent)
                )
                results[entry.project_name] = ok
                if ok:
                    updated.append(entry.project_name)
                continue
            ok, changed = self._pull_existing(entry, target_path, sparse_subpaths)
            results[entry.project_name] = ok
            if ok and changed:
                updated.append(entry.project_name)
        return results, updated
