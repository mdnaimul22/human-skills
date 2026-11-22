from __future__ import annotations
from src.config import Settings, get_rel_path, setup_logger
from src.apps.git.schema import ForwardRule, UpstreamEntry

logger = setup_logger(Settings.LOG_DIR / "git.log", name="apps.git.helpers.classifier")


class ChangeClassifier:
    def __init__(self, forwards: list[ForwardRule], upstreams: list[UpstreamEntry], repo_root: str = "") -> None:
        self.forwards = forwards
        self.upstreams = upstreams
        self.repo_root = repo_root

    def classify_managed(self, status_output: str) -> dict[str, list[str]]:
        upstream_changes: dict[str, list[str]] = {}
        for line in status_output.splitlines():
            if len(line) < 4:
                continue
            changed_file = line[3:].strip().strip('"')
            if " -> " in changed_file:
                changed_file = changed_file.split(" -> ")[-1].strip('"')
            changed_rel = get_rel_path(changed_file, self.repo_root)
            matched_upstream = self._match_to_upstream(changed_rel)
            if matched_upstream:
                upstream_changes.setdefault(matched_upstream, []).append(changed_file)
        return upstream_changes

    def _match_to_upstream(self, changed_rel: str) -> str | None:
        up_id_map = {u.upstream_id: u.project_name for u in self.upstreams if u.upstream_id}
        up_name_set = {u.project_name for u in self.upstreams if u.project_name}
        for rule in self.forwards:
            if not rule.enabled or not rule.to_path:
                continue
            dst_rel = get_rel_path(rule.to_path, self.repo_root).rstrip("/")
            if changed_rel != dst_rel and not changed_rel.startswith(f"{dst_rel}/"):
                continue
            resolved = self._resolve_rule_owner(rule, up_id_map, up_name_set)
            if resolved:
                return resolved
        return None

    def _resolve_rule_owner(
        self,
        rule: ForwardRule,
        up_id_map: dict[str, str],
        up_name_set: set[str],
    ) -> str | None:
        if rule.upstream_id and rule.upstream_id in up_id_map:
            return up_id_map[rule.upstream_id]
        if rule.project_name and rule.project_name in up_name_set:
            return rule.project_name
        if rule.from_path:
            src_rel = get_rel_path(rule.from_path, self.repo_root).rstrip("/")
            for up in self.upstreams:
                up_rel = get_rel_path(up.path, self.repo_root).rstrip("/")
                if src_rel == up_rel or src_rel.startswith(f"{up_rel}/"):
                    return up.project_name
        return None

    @staticmethod
    def filter_staged_deletions(files: list[str], status_output: str) -> list[str]:
        if not status_output:
            return files
        staged_deletions: set[str] = set()
        for line in status_output.splitlines():
            if len(line) < 4:
                continue
            if line[0] == "D":
                path = line[3:].strip().strip('"')
                if " -> " in path:
                    path = path.split(" -> ")[-1].strip('"')
                staged_deletions.add(path)
        return [f for f in files if f not in staged_deletions]
