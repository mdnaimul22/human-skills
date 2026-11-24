from __future__ import annotations
import subprocess
import time
import pytest
from src.apps.git import (
    ForwardRule, GitConfig, GitManager, ProjectCreate, ProjectUpdate,
    ScheduleConfig, UpstreamEntry,
)
from src.helpers import NotFoundError


def _git(cwd: str, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _init_git_identity(repo_dir: str) -> None:
    _git(repo_dir, "config", "user.email", "test@app.local")
    _git(repo_dir, "config", "user.name", "App Tester")


def _setup_local_git_fixture(tmp_path) -> tuple[str, str, str, str]:
    upstream_bare = tmp_path / "upstream.git"
    upstream_work = tmp_path / "upstream_work"
    target_bare = tmp_path / "target.git"
    target_work = tmp_path / "target_work"

    upstream_bare.mkdir()
    _git(str(upstream_bare), "init", "--bare", "-b", "main")

    _git(str(tmp_path), "clone", str(upstream_bare), str(upstream_work))
    _init_git_identity(str(upstream_work))
    (upstream_work / "scripts").mkdir()
    (upstream_work / "scripts" / "tool_a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (upstream_work / "scripts" / "old_tool.py").write_text("OLD = True\n", encoding="utf-8")
    (upstream_work / "heavy_unused").mkdir()
    (upstream_work / "heavy_unused" / "ignored.bin").write_bytes(b"0" * 1024)
    _git(str(upstream_work), "add", ".")
    _git(str(upstream_work), "commit", "-m", "init upstream")
    _git(str(upstream_work), "push", "-u", "origin", "main")

    target_bare.mkdir()
    _git(str(target_bare), "init", "--bare", "-b", "main")
    _git(str(tmp_path), "clone", str(target_bare), str(target_work))
    _init_git_identity(str(target_work))
    (target_work / "README.md").write_text("# Target Repo\n", encoding="utf-8")
    (target_work / ".gitignore").write_text("vendor/\n", encoding="utf-8")
    _git(str(target_work), "add", ".")
    _git(str(target_work), "commit", "-m", "init target")
    _git(str(target_work), "push", "-u", "origin", "main")

    return str(upstream_bare), str(upstream_work), str(target_bare), str(target_work)


@pytest.fixture(autouse=True)
def _reset_git_manager() -> None:
    GitManager.reset_instance()
    yield
    GitManager.reset_instance()


def test_e2e_sparse_clone_scoped_surgical_commit_and_orphan_cleanup(tmp_path) -> None:
    upstream_bare, upstream_work, target_bare, target_work = _setup_local_git_fixture(tmp_path)
    data_dir = str(tmp_path / "data_gitsync")
    mgr = GitManager(data_dir=data_dir)

    meta = mgr.create_project(ProjectCreate(name="App Worker", path=target_work))
    up = UpstreamEntry(
        project_name="ffmpeg-skill",
        upstream_id="ff01",
        branch="main",
        sparse=True,
        blobless=False,
        path="vendor/ffmpeg-skill",
        url=upstream_bare,
    )
    fwd = ForwardRule(
        enabled=True,
        upstream_id="ff01",
        forward_id="fw01",
        from_path="vendor/ffmpeg-skill/scripts",
        to_path="managed/scripts",
    )
    mgr.update_project(
        meta.id,
        ProjectUpdate(
            upstreams=[up],
            forwards=[fwd],
            git=GitConfig(auto_push=True, branch="main"),
            schedule=ScheduleConfig(interval_minutes=10, poll_interval_seconds=1),
        ),
    )

    backend_untracked = tmp_path / "target_work" / "app_backend_untracked.py"
    backend_untracked.write_text("# must stay untracked\n", encoding="utf-8")
    backend_staged = tmp_path / "target_work" / "app_backend_staged.py"
    backend_staged.write_text("# must stay staged and uncommitted\n", encoding="utf-8")
    _git(target_work, "add", "app_backend_staged.py")

    callback_events = []
    mgr.register_sync_callback(meta.id, lambda res: callback_events.append(res))

    res1 = mgr.sync_project(meta.id)
    assert res1.push_ok
    assert res1.pull_results == {"ffmpeg-skill": True}
    assert res1.committed_upstreams == ["ffmpeg-skill"]
    assert len(callback_events) == 1

    res_noop = mgr.sync_project(meta.id)
    assert res_noop.copied_targets == []
    assert res_noop.removed_orphans == []
    assert len(callback_events) == 1
    assert not list((tmp_path / "target_work" / "managed" / "scripts").glob("*.tmp"))

    assert (tmp_path / "target_work" / "vendor" / "ffmpeg-skill" / "scripts" / "tool_a.py").is_file()
    assert not (tmp_path / "target_work" / "vendor" / "ffmpeg-skill" / "heavy_unused").exists()
    assert (tmp_path / "target_work" / "managed" / "scripts" / "tool_a.py").read_text(encoding="utf-8") == "VALUE = 1\n"

    last_committed_files = _git(target_bare, "show", "--name-only", "--pretty=format:", "main").splitlines()
    assert set(last_committed_files) == {"managed/scripts/tool_a.py", "managed/scripts/old_tool.py"}

    status_after = _git(target_work, "status", "--porcelain")
    assert "A  app_backend_staged.py" in status_after
    assert "?? app_backend_untracked.py" in status_after

    (tmp_path / "upstream_work" / "scripts" / "tool_a.py").write_text("VALUE = 2\n", encoding="utf-8")
    (tmp_path / "upstream_work" / "scripts" / "old_tool.py").unlink()
    _git(upstream_work, "add", "-A")
    _git(upstream_work, "commit", "-m", "update tool_a and delete old_tool")
    _git(upstream_work, "push", "origin", "main")

    res2 = mgr.sync_project(meta.id)
    assert res2.push_ok
    assert len(callback_events) == 2
    assert (tmp_path / "target_work" / "managed" / "scripts" / "tool_a.py").read_text(encoding="utf-8") == "VALUE = 2\n"
    assert not (tmp_path / "target_work" / "managed" / "scripts" / "old_tool.py").exists()

    mgr.update_project(meta.id, ProjectUpdate(forwards=[]))
    res3 = mgr.sync_project(meta.id)
    assert res3.push_ok
    assert len(callback_events) == 3
    assert res3.removed_orphans == ["managed/scripts"]
    assert not (tmp_path / "target_work" / "managed" / "scripts").exists()

    status_final = _git(target_work, "status", "--porcelain")
    assert "A  app_backend_staged.py" in status_final
    assert "?? app_backend_untracked.py" in status_final


@pytest.mark.asyncio
async def test_async_bridge_and_worker_lifecycle(tmp_path) -> None:
    upstream_bare, _, _, target_work = _setup_local_git_fixture(tmp_path)
    mgr = GitManager(data_dir=str(tmp_path / "data_gitsync"))
    meta = mgr.create_project(ProjectCreate(name="Async Sync", path=target_work))
    up = UpstreamEntry(
        project_name="ffmpeg-skill",
        upstream_id="ff02",
        branch="main",
        sparse=True,
        blobless=False,
        path="vendor/ffmpeg-skill",
        url=upstream_bare,
    )
    fwd = ForwardRule(
        enabled=True,
        upstream_id="ff02",
        forward_id="fw02",
        from_path="vendor/ffmpeg-skill/scripts",
        to_path="managed/scripts",
    )
    mgr.update_project(
        meta.id,
        ProjectUpdate(
            upstreams=[up],
            forwards=[fwd],
            git=GitConfig(auto_push=False, branch="main"),
            schedule=ScheduleConfig(interval_minutes=10, poll_interval_seconds=1),
        ),
    )

    result = await mgr.sync_project_async(meta.id)
    assert result.push_ok
    assert mgr.get_project(meta.id).last_result is not None

    assert mgr.start_project(meta.id) is True
    assert mgr.is_running(meta.id) is True
    assert mgr.start_project(meta.id) is False
    assert mgr.trigger_sync(meta.id) is True
    time.sleep(0.1)
    assert mgr.stop_project(meta.id) is True
    assert mgr.is_running(meta.id) is False

    mgr.delete_project(meta.id)
    with pytest.raises(NotFoundError):
        mgr.get_project(meta.id)


def test_branch_head_pushes_active_branch_and_mismatch_fails_fast(tmp_path) -> None:
    upstream_bare, _, target_bare, target_work = _setup_local_git_fixture(tmp_path)
    _git(target_work, "checkout", "-b", "development")
    _git(target_work, "push", "-u", "origin", "development")

    mgr = GitManager(data_dir=str(tmp_path / "data_gitsync"))
    meta = mgr.create_project(ProjectCreate(name="Branch Sync", path=target_work))
    up = UpstreamEntry(
        project_name="ffmpeg-skill",
        upstream_id="ff03",
        branch="main",
        sparse=True,
        blobless=False,
        path="vendor/ffmpeg-skill",
        url=upstream_bare,
    )
    fwd = ForwardRule(
        enabled=True,
        upstream_id="ff03",
        forward_id="fw03",
        from_path="vendor/ffmpeg-skill/scripts",
        to_path="managed/scripts",
    )
    mgr.update_project(
        meta.id,
        ProjectUpdate(
            upstreams=[up],
            forwards=[fwd],
            git=GitConfig(auto_commit=True, auto_push=True, branch="main"),
            schedule=ScheduleConfig(interval_minutes=10, poll_interval_seconds=1),
        ),
    )

    res_mismatch = mgr.sync_project(meta.id)
    assert res_mismatch.push_ok is False
    assert res_mismatch.committed_upstreams == []
    assert _git(target_work, "rev-list", "--count", "HEAD..HEAD") == "0"
    main_head_before = _git(target_bare, "rev-parse", "main")
    dev_head_before = _git(target_bare, "rev-parse", "development")
    assert _git(target_work, "rev-parse", "HEAD") == dev_head_before

    mgr.update_project(
        meta.id,
        ProjectUpdate(git=GitConfig(auto_commit=True, auto_push=True, branch="HEAD")),
    )
    res_head = mgr.sync_project(meta.id)
    assert res_head.push_ok is True
    assert res_head.committed_upstreams == ["ffmpeg-skill"]

    assert _git(target_bare, "rev-parse", "main") == main_head_before
    committed_dev = _git(target_bare, "show", "--name-only", "--pretty=format:", "development").splitlines()
    assert set(committed_dev) == {"managed/scripts/tool_a.py", "managed/scripts/old_tool.py"}
    assert _git(target_work, "rev-parse", "HEAD") == _git(target_bare, "rev-parse", "development")
