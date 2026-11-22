from __future__ import annotations
import filecmp
from functools import partial
import json
import os
import shutil
import uuid
from pydantic import ValidationError as PydanticValidationError
from src.config import (
    Settings, delete, ensure_dir, exists, get_abs_path, get_mtime,
    get_rel_path, get_size, is_dir, is_file, is_subpath, read_json,
    setup_logger, write_json,
)
from src.helpers import ValidationError, get_now_iso
from src.apps.git.providers import run_git
from src.apps.git.schema import (
    ForwardRule, MEMORY_LIST_ADAPTER, MemoryEntry, UpstreamEntry, generate_hash_id,
)
from .orphan import OrphanEngine

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.forwarder")


def load_memory(rel: str) -> list[MemoryEntry]:
    if not exists(rel):
        return []
    try:
        return MEMORY_LIST_ADAPTER.validate_python(read_json(rel))
    except (OSError, json.JSONDecodeError, PydanticValidationError) as e:
        logger.error(f"Failed to parse memory from {rel}: {e}")
        raise ValidationError(f"Corrupted memory file '{rel}': {e}") from e


def save_memory(entries: list[MemoryEntry], rel: str) -> None:
    write_json(rel, [e.model_dump(by_alias=True) for e in entries])


class ForwardEngine:
    def __init__(self, repo_root: str = "") -> None:
        self.repo_root = repo_root
        self.orphan_engine = OrphanEngine(repo_root=repo_root)

    def _resolve_path(self, raw_path: str) -> str:
        if self.repo_root and not raw_path.startswith("/"):
            return get_abs_path(self.repo_root, raw_path)
        return get_abs_path(raw_path)

    def _guard_managed_target(self, target_abs: str) -> None:
        if not self.repo_root:
            return
        if not is_subpath(self.repo_root, target_abs):
            raise ValidationError(f"Target path escapes repository root: {target_abs}")
        rel = get_rel_path(target_abs, self.repo_root).strip("/")
        if rel in ("", ".", ".git") or rel.startswith(".git/"):
            raise ValidationError(f"Refusing to modify protected repository path: {target_abs}")

    @staticmethod
    def should_copy(src_path: str, dst_path: str) -> bool:
        if not exists(dst_path):
            return True
        if get_size(src_path) != get_size(dst_path):
            return True
        if get_mtime(src_path) > get_mtime(dst_path):
            return True
        return not filecmp.cmp(get_abs_path(src_path), get_abs_path(dst_path), shallow=False)

    @staticmethod
    def ignore_copy_patterns(path: str, names: list[str]) -> set[str]:
        return {name for name in names if name in (".git", "__pycache__") or name.endswith(".pyc")}

    @staticmethod
    def atomic_copy(src: str, dst: str) -> str:
        abs_src = get_abs_path(src)
        abs_dst = get_abs_path(dst)
        parent, fname = abs_dst.rsplit("/", 1)
        ensure_dir(parent)
        tmp_dst = f"{parent}/.{fname}.{os.getpid()}.{uuid.uuid4().hex[:6]}.tmp"
        try:
            shutil.copy2(abs_src, tmp_dst)
            os.replace(tmp_dst, abs_dst)
        except OSError:
            if exists(tmp_dst):
                delete(tmp_dst)
            raise
        return abs_dst

    @staticmethod
    def incremental_copy(src: str, dst: str) -> str:
        if is_file(src) and is_file(dst) and not ForwardEngine.should_copy(src, dst):
            return dst
        return ForwardEngine.atomic_copy(src, dst)

    def prune_extraneous(self, src_dir: str, dst_dir: str) -> list[str]:
        abs_src = get_abs_path(src_dir)
        abs_dst = get_abs_path(dst_dir)
        if not exists(abs_dst):
            return []
        self._guard_managed_target(abs_dst)
        pruned: list[str] = []
        git_dir = f"{abs_dst}/.git"
        if exists(git_dir):
            delete(git_dir)
            pruned.append(get_rel_path(git_dir, self.repo_root) if self.repo_root else git_dir)
        for root, dirs, files in os.walk(abs_dst, topdown=True):
            rel_to_dst = get_rel_path(root, abs_dst)
            src_equiv = abs_src if rel_to_dst in (".", "") else f"{abs_src}/{rel_to_dst}"
            pruned.extend(self._prune_level_files(root, files, src_equiv))
            pruned.extend(self._prune_level_dirs(root, dirs, src_equiv))
        return pruned

    def _prune_level_files(self, root: str, files: list[str], src_equiv: str) -> list[str]:
        removed: list[str] = []
        for fname in files:
            if fname.endswith(".pyc"):
                continue
            dst_file = f"{root}/{fname}"
            if not exists(f"{src_equiv}/{fname}"):
                delete(dst_file)
                removed.append(get_rel_path(dst_file, self.repo_root) if self.repo_root else dst_file)
        return removed

    def _prune_level_dirs(self, root: str, dirs: list[str], src_equiv: str) -> list[str]:
        removed: list[str] = []
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        removable = [d for d in dirs if d == ".git" or not exists(f"{src_equiv}/{d}")]
        for dname in removable:
            dst_subdir = f"{root}/{dname}"
            delete(dst_subdir)
            removed.append(get_rel_path(dst_subdir, self.repo_root) if self.repo_root else dst_subdir)
            dirs.remove(dname)
        return removed

    def create_memory_entry(self, rule: ForwardRule) -> MemoryEntry:
        return MemoryEntry(
            memory_id=generate_hash_id(),
            upstream_id=rule.upstream_id,
            forward_id=rule.forward_id,
            project_name=rule.project_name,
            from_path=get_rel_path(rule.from_path, self.repo_root),
            to_path=get_rel_path(rule.to_path, self.repo_root),
            last_synced=get_now_iso(),
        )

    def _find_matching_upstream(
        self,
        src: str,
        rule: ForwardRule,
        upstreams: list[UpstreamEntry],
    ) -> UpstreamEntry | None:
        if rule.upstream_id:
            for up in upstreams:
                if up.upstream_id == rule.upstream_id:
                    return up
        for up in upstreams:
            up_abs = self._resolve_path(up.path)
            if src == up_abs or src.startswith(f"{up_abs}/"):
                return up
        return None

    def resolve_missing_source(self, src: str, rule: ForwardRule, upstreams: list[UpstreamEntry]) -> bool:
        matched = self._find_matching_upstream(src, rule, upstreams)
        if matched is None:
            logger.warning(f"Source missing with no matching upstream: {src}")
            return False
        up_abs = self._resolve_path(matched.path)
        if not exists(up_abs):
            logger.warning(f"Upstream repository path missing: {up_abs}")
            return False
        rel_in_up = get_rel_path(src, up_abs)
        has_head = run_git(["cat-file", "-e", f"HEAD:{rel_in_up}"], up_abs).ok
        if not has_head and matched.url and matched.branch:
            fetch_cmd = ["fetch", "origin", matched.branch]
            if matched.blobless:
                fetch_cmd.append("--filter=blob:none")
            run_git(fetch_cmd, up_abs)
            if run_git(["cat-file", "-e", f"origin/{matched.branch}:{rel_in_up}"], up_abs).ok:
                run_git(["reset", "--hard", f"origin/{matched.branch}"], up_abs)
                has_head = True
        if not has_head:
            logger.warning(f"Upstream source path does not exist in git tree: {src}")
            return False
        if matched.sparse:
            run_git(["sparse-checkout", "add", "--skip-checks", rel_in_up], up_abs)
        else:
            run_git(["checkout", "HEAD", "--", rel_in_up], up_abs)
        return exists(src)

    def _copy_file_rule(self, src: str, dst: str, name: str) -> bool:
        if is_dir(dst) or dst.endswith("/") or dst.endswith("\\"):
            ensure_dir(dst)
            actual_dst = f"{dst.rstrip('/')}/{name}"
        else:
            ensure_dir(dst.rsplit("/", 1)[0])
            actual_dst = dst
        self._guard_managed_target(actual_dst)
        if not self.should_copy(src, actual_dst):
            return False
        self.atomic_copy(src, actual_dst)
        return True

    def _tracked_copy_file(self, copied_files: list[str], src_file: str, dst_file: str) -> str:
        if is_file(src_file) and is_file(dst_file) and not self.should_copy(src_file, dst_file):
            return dst_file
        copied_files.append(dst_file)
        return self.atomic_copy(src_file, dst_file)

    def _copy_dir_rule(self, src: str, dst: str) -> bool:
        self._guard_managed_target(dst)
        ensure_dir(dst)
        if self.repo_root:
            rel_dst = get_rel_path(dst, self.repo_root)
            ls_res = run_git(["ls-files", "-s", rel_dst], self.repo_root)
            if ls_res.ok and ls_res.output.startswith("160000"):
                logger.warning(f"Destination {rel_dst} is tracked as a git submodule — untracking")
                run_git(["rm", "--cached", rel_dst], self.repo_root)

        copied_files: list[str] = []
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            copy_function=partial(self._tracked_copy_file, copied_files),
            ignore=self.ignore_copy_patterns,
        )
        pruned = self.prune_extraneous(src, dst)
        if self.repo_root and pruned:
            for path in pruned:
                run_git(["rm", "-r", "-f", "--cached", "--quiet", path], self.repo_root)
        return bool(copied_files or pruned)

    def forward(
        self,
        forwards: list[ForwardRule],
        upstreams: list[UpstreamEntry],
    ) -> tuple[list[str], list[MemoryEntry]]:
        copied: list[str] = []
        current_memory: list[MemoryEntry] = []
        for rule in forwards:
            if not rule.enabled or not rule.from_path or not rule.to_path:
                continue
            src = self._resolve_path(rule.from_path)
            dst = self._resolve_path(rule.to_path)
            if not exists(src) and not self.resolve_missing_source(src, rule, upstreams):
                continue
            name = rule.from_path.rstrip("/").rsplit("/", 1)[-1]
            current_memory.append(self.create_memory_entry(rule))
            if is_file(src):
                if self._copy_file_rule(src, dst, name):
                    copied.append(name)
            elif is_dir(src):
                if self._copy_dir_rule(src, dst):
                    copied.append(name)
        return copied, current_memory

    def cleanup_orphans(
        self,
        previous: list[MemoryEntry],
        current: list[ForwardRule],
        upstreams: list[UpstreamEntry],
    ) -> list[str]:
        removed_paths: list[str] = []
        orphans = self.orphan_engine.detect_orphans(previous, current, upstreams)
        for orphan_rel in sorted(orphans):
            orphan_abs = self._resolve_path(orphan_rel)
            self._guard_managed_target(orphan_abs)
            removed_any = False
            rel_repo = (
                get_rel_path(orphan_abs, self.repo_root)
                if self.repo_root
                else orphan_rel.lstrip("/")
            )
            if self.repo_root:
                rm_res = run_git(["rm", "-r", "-f", "--cached", "--quiet", rel_repo], self.repo_root)
                if rm_res.ok:
                    removed_any = True
            if exists(orphan_abs):
                delete(orphan_abs)
                removed_any = True
            if removed_any:
                removed_paths.append(rel_repo)
                logger.info(f"Removed orphaned target: {rel_repo}")
        return removed_paths
