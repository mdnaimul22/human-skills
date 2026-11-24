from __future__ import annotations
import time
import pytest
from src.config import Settings, write_text
from src.helpers import NotFoundError, ValidationError
from src.apps.git.helpers import (
    ChangeClassifier, ConfigWatcher, ForwardEngine, OrphanEngine,
    ProjectRegistry, UpstreamResolver, load_memory,
)
from src.apps.git.schema import (
    ForwardRule, MemoryEntry, ProjectCreate, ProjectUpdate, UpstreamEntry,
)


def test_gitsync_settings_initialized_from_env_control_panel() -> None:
    assert Settings.RAW_GITSYNC_DATA_DIR == "data/gitsync"
    assert Settings.GITSYNC_DATA_DIR == Settings.DATA_DIR / "gitsync"
    assert Settings.GIT_BRANCH == "main"
    assert Settings.SYNC_INTERVAL_MINUTES >= 1
    assert Settings.SYNC_POLL_SECONDS >= 1


def test_classifier_ignores_unrelated_app_backend_files() -> None:
    up = UpstreamEntry(project_name="ffmpeg-skill", upstream_id="up01", path="upstream/ffmpeg-skill")
    fwd = ForwardRule(
        enabled=True,
        project_name="ffmpeg-skill",
        upstream_id="up01",
        forward_id="fw01",
        from_path="upstream/ffmpeg-skill/scripts",
        to_path="src/core/ffmpeg/upstream/scripts",
    )
    classifier = ChangeClassifier([fwd], [up], repo_root="/repo")
    status_output = "\n".join([
        "?? src/core/ffmpeg/upstream/scripts/cut.py",
        " M src/routers/tools.py",
        "A  src/services/metadata.py",
        " M main.py",
    ])
    managed = classifier.classify_managed(status_output)
    assert managed == {"ffmpeg-skill": ["src/core/ffmpeg/upstream/scripts/cut.py"]}


def test_upstream_resolver_extracts_sparse_subpaths() -> None:
    up = UpstreamEntry(project_name="ffmpeg-skill", upstream_id="up01", path="vendor/ffmpeg-skill")
    forwards = [
        ForwardRule(upstream_id="up01", from_path="vendor/ffmpeg-skill/scripts", to_path="dst/scripts"),
        ForwardRule(upstream_id="up01", from_path="vendor/ffmpeg-skill/templates", to_path="dst/templates"),
        ForwardRule(enabled=False, upstream_id="up01", from_path="vendor/ffmpeg-skill/docs", to_path="dst/docs"),
    ]
    subpaths = UpstreamResolver.resolve_sparse_subpaths(up, forwards, repo_root="/repo")
    assert subpaths == ["scripts", "templates"]


def test_orphan_engine_detects_all_lineage_removals() -> None:
    engine = OrphanEngine(repo_root="/repo")
    up_keep = UpstreamEntry(project_name="keep", upstream_id="u1", path="up/keep")
    previous = [
        MemoryEntry(upstream_id="u_deleted", forward_id="f1", from_path="up/gone/a", to_path="dst/gone"),
        MemoryEntry(upstream_id="u1", forward_id="f_removed", from_path="up/keep/b", to_path="dst/removed"),
        MemoryEntry(upstream_id="u1", forward_id="f_renamed", from_path="up/keep/c", to_path="dst/old_name"),
        MemoryEntry(upstream_id="u1", forward_id="f_src_changed", from_path="up/keep/v1", to_path="dst/same"),
        MemoryEntry(upstream_id="u1", forward_id="f_stable", from_path="up/keep/ok", to_path="dst/ok"),
    ]
    current = [
        ForwardRule(upstream_id="u1", forward_id="f_renamed", from_path="up/keep/c", to_path="dst/new_name"),
        ForwardRule(upstream_id="u1", forward_id="f_src_changed", from_path="up/keep/v2", to_path="dst/same"),
        ForwardRule(upstream_id="u1", forward_id="f_stable", from_path="up/keep/ok", to_path="dst/ok"),
    ]
    orphans = engine.detect_orphans(previous, current, [up_keep])
    assert orphans == {"dst/gone", "dst/removed", "dst/old_name", "dst/same"}


def test_project_registry_crud_and_fail_fast_errors(tmp_path) -> None:
    registry = ProjectRegistry(data_dir=str(tmp_path / "gitsync"))
    meta = registry.create(ProjectCreate(name="FFmpeg Sync", path=str(tmp_path / "repo")))
    assert meta.id == "ffmpeg-sync"

    dup = registry.create(ProjectCreate(name="FFmpeg Sync", path=str(tmp_path / "repo2")))
    assert dup.id == "ffmpeg-sync-1"

    up = UpstreamEntry(project_name="ffmpeg-skill", upstream_id="up1", path="up/ff", url="https://example.com/ff.git")
    fwd = ForwardRule(upstream_id="up1", from_path="up/ff/scripts", to_path="managed/scripts")
    updated = registry.update(meta.id, ProjectUpdate(upstreams=[up], forwards=[fwd]))
    assert len(updated.upstreams) == 1
    assert updated.forwards[0].project_name == "ffmpeg-skill"

    registry.delete(meta.id)
    with pytest.raises(NotFoundError):
        registry.get(meta.id)
    with pytest.raises(NotFoundError):
        registry.delete("nonexistent-project")


def test_config_watcher_hot_reload_and_corrupted_json_raises(tmp_path) -> None:
    data_dir = str(tmp_path / "gitsync")
    registry = ProjectRegistry(data_dir=data_dir)
    meta = registry.create(ProjectCreate(name="Watch Test", path=str(tmp_path / "repo")))
    watcher = ConfigWatcher(meta.id, meta.path, data_dir=data_dir)
    assert not watcher.has_changed()

    time.sleep(0.02)
    up = UpstreamEntry(project_name="alpha", upstream_id="u1", path="up/alpha")
    registry.update(meta.id, ProjectUpdate(upstreams=[up]))
    assert watcher.has_changed()
    diff = watcher.reload()
    assert diff.has_changes
    assert diff.upstreams_before == 0
    assert diff.upstreams_after == 1

    write_text(f"{data_dir}/{meta.id}/upstream.json", "{corrupted json")
    with pytest.raises(ValidationError):
        watcher.reload()

    write_text(f"{data_dir}/{meta.id}/memory.json", "{corrupted")
    with pytest.raises(ValidationError):
        load_memory(f"{data_dir}/{meta.id}/memory.json")


def test_forward_engine_blocks_path_traversal_and_git_dir(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    src_file = tmp_path / "source.py"
    src_file.write_text("print('hi')\n", encoding="utf-8")

    engine = ForwardEngine(repo_root=str(repo))
    escape_rule = ForwardRule(from_path=str(src_file), to_path=str(tmp_path / "outside.py"))
    with pytest.raises(ValidationError):
        engine.forward([escape_rule], [])

    git_rule = ForwardRule(from_path=str(src_file), to_path=".git/config")
    with pytest.raises(ValidationError):
        engine.forward([git_rule], [])


def test_forward_engine_ignores_pycache_no_spurious_copies(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    src_dir = repo / "vendor" / "scripts"
    src_dir.mkdir(parents=True)
    (src_dir / "tool.py").write_text("X = 1\n", encoding="utf-8")

    up = UpstreamEntry(project_name="ffmpeg-skill", upstream_id="up_pyc", path="vendor")
    rule = ForwardRule(
        enabled=True,
        upstream_id="up_pyc",
        forward_id="fw_pyc",
        from_path="vendor/scripts",
        to_path="scripts/ffmpeg/scripts",
    )
    engine = ForwardEngine(repo_root=str(repo))

    copied1, _ = engine.forward([rule], [up])
    assert copied1 == ["scripts"]

    pycache_dir = repo / "scripts" / "ffmpeg" / "scripts" / "__pycache__"
    pycache_dir.mkdir(parents=True)
    pyc_file = pycache_dir / "tool.cpython-313.pyc"
    pyc_file.write_bytes(b"pyc-bytes")

    copied2, _ = engine.forward([rule], [up])
    assert copied2 == []
    assert pyc_file.is_file()
