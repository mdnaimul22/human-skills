from __future__ import annotations
from src.config import Settings, get_rel_path, setup_logger
from src.apps.git.schema import ForwardRule, MemoryEntry, UpstreamEntry

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.orphan")


class OrphanEngine:
    def __init__(self, repo_root: str = "") -> None:
        self.repo_root = repo_root

    def detect_orphans(
        self,
        previous: list[MemoryEntry],
        current: list[ForwardRule],
        upstreams: list[UpstreamEntry],
    ) -> set[str]:
        orphans: set[str] = set()
        active_upstream_ids = {u.upstream_id for u in upstreams if u.upstream_id}
        active_forward_map = {f.forward_id: f for f in current if f.enabled and f.forward_id}
        active_dsts = {get_rel_path(f.to_path, self.repo_root) for f in current if f.enabled and f.to_path}

        for entry in previous:
            if not entry.to_path:
                continue
            if self._is_entry_orphaned(entry, active_upstream_ids, active_forward_map, active_dsts):
                orphans.add(entry.to_path)
        return orphans

    def _is_entry_orphaned(
        self,
        entry: MemoryEntry,
        active_upstream_ids: set[str],
        active_forward_map: dict[str, ForwardRule],
        active_dsts: set[str],
    ) -> bool:
        entry_to = get_rel_path(entry.to_path, self.repo_root)
        entry_from = get_rel_path(entry.from_path, self.repo_root)

        if entry.upstream_id and entry.upstream_id not in active_upstream_ids:
            return True
        if entry.forward_id and entry.forward_id not in active_forward_map:
            return entry_to not in active_dsts
        if entry.forward_id in active_forward_map:
            rule = active_forward_map[entry.forward_id]
            curr_to = get_rel_path(rule.to_path, self.repo_root)
            curr_from = get_rel_path(rule.from_path, self.repo_root)
            if curr_to != entry_to or curr_from != entry_from:
                return True
        return False
