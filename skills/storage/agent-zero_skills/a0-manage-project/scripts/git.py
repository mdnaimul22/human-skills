import os
import sys
import re
import time
import base64
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

try:
    from . import files
except ImportError:
    try:
        import files
    except ImportError:
        from helpers import files  # type: ignore

try:
    from helpers.localization import Localization
except ImportError:
    class Localization:
        @classmethod
        def get(cls):
            return cls()
        def get_tzinfo(self):
            return timezone.utc

try:
    from git import Git, Repo
    HAS_GITPYTHON = True
except ImportError:
    Git = None  # type: ignore
    Repo = None  # type: ignore
    HAS_GITPYTHON = False

try:
    from giturlparse import parse as _giturlparse_parse
    HAS_GITURLPARSE = True
except ImportError:
    HAS_GITURLPARSE = False


def strip_auth_from_url(url: str) -> str:
    """Remove any authentication info from URL."""
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.hostname:
        return url
    clean_netloc = parsed.hostname
    if parsed.port:
        clean_netloc += f":{parsed.port}"
    return urlunparse((parsed.scheme, clean_netloc, parsed.path, '', '', ''))


def extract_author_repo(url: str) -> Tuple[str, str]:
    """Extract owner/author and repository name from Git URL."""
    clean_url = strip_auth_from_url(url.strip())
    
    if HAS_GITURLPARSE:
        try:
            parsed = _giturlparse_parse(clean_url)
            author = (parsed.owner or "").strip()
            repo = (parsed.repo or parsed.name or "").strip()
            if repo.endswith(".git"):
                repo = repo[:-4]
            if author and repo:
                return author, repo
        except Exception:
            pass

    # Regex fallback
    # Matches https://github.com/owner/repo.git or git@github.com:owner/repo.git
    m = re.search(r"[:/]([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?/?$", clean_url)
    if m:
        author = m.group(1).strip()
        repo = m.group(2).strip()
        return author, repo

    raise ValueError(f"Could not derive author and repository name from URL: {url}")


@dataclass
class GitHeadInfo:
    hash: str
    short_hash: str
    message: str
    author: str
    committed_at: str
    authored_at: str


@dataclass
class GitReleaseInfo:
    tag: str
    short_tag: str
    version: str
    released_at: str


@dataclass
class GitRemoteReleaseInfo:
    tag: str
    commit_hash: str
    short_commit_hash: str
    released_at: str


@dataclass
class GitRemoteReleasesResult:
    is_git_repo: bool
    is_remote: bool
    author: str
    repo: str
    releases: List[GitRemoteReleaseInfo]
    error: str = ""


@dataclass
class GitRemoteCommitsInfo:
    is_git_repo: bool
    is_remote: bool
    path: str
    branch: str
    remote_branch: str
    commits_since_local: int
    last_remote_commit_at: str
    error: str = ""


@dataclass
class GitRepoReleaseInfo:
    is_git_repo: bool
    is_remote: bool
    path: str
    author: str
    repo: str
    branch: str
    head: Optional[GitHeadInfo]
    release: Optional[GitReleaseInfo]
    error: str = ""


def _format_git_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).strftime('%Y-%m-%d %H:%M:%S')


def _split_describe_version(describe: str) -> Tuple[str, int]:
    normalized = describe.strip()
    match = re.fullmatch(r"(.+)-(\d+)-g[0-9a-f]+", normalized)
    if not match:
        return normalized, 0
    return match.group(1), int(match.group(2))


def _format_release_version(
    branch: str,
    short_tag: str,
    commits_since_tag: int,
    commit_hash: str,
) -> str:
    version_prefix = branch[0].upper() if branch else "D"
    version_core = short_tag or commit_hash[:7]

    if (
        short_tag
        and commits_since_tag > 0
        and branch.strip().lower() != "main"
    ):
        version_core = f"{short_tag}+{commits_since_tag}"

    return f"{version_prefix} {version_core}"


def clone_repo(url: str, dest: str, token: Optional[str] = None) -> None:
    """Clone a git repository. Uses http.extraHeader for token auth (never stored in URL/config)."""
    cmd = ['git']
    
    if token:
        # GitHub Git HTTP requires Basic Auth, not Bearer
        auth_string = f"x-access-token:{token}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()
        cmd.extend(['-c', f'http.extraHeader=Authorization: Basic {auth_base64}'])
    
    cmd.extend(['clone', '--progress', '--', url, dest])
    
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        clean_url = strip_auth_from_url(url)
        err = result.stderr.strip() or result.stdout.strip() or f"Git exit code: {result.returncode}"
        raise RuntimeError(f"Failed to clone repository from {clean_url}: {err}")


def get_repo_status(repo_path: str) -> Dict[str, Any]:
    """
    Get git status for a repository, filtering out .a0proj internal metadata files.
    Works with subprocess or GitPython.
    """
    try:
        if not os.path.exists(repo_path) or not os.path.exists(os.path.join(repo_path, ".git")):
            return {"is_git_repo": False, "error": "Not a git repository"}

        # Use subprocess git for universal reliability
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'

        # 1. Current branch
        branch_res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path, capture_output=True, text=True, env=env
        )
        current_branch = branch_res.stdout.strip() or "HEAD"

        # 2. Remote URL
        remote_res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_path, capture_output=True, text=True, env=env
        )
        remote_url = strip_auth_from_url(remote_res.stdout.strip())

        # 3. Status --porcelain
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path, capture_output=True, text=True, env=env
        )
        
        status_lines = [line for line in status_res.stdout.splitlines() if line.strip()]
        
        # Filter out .a0proj files
        real_changes = []
        real_untracked = []
        for line in status_lines:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                status_code, filename = parts
                if ".a0proj" in filename:
                    continue
                if status_code == "??":
                    real_untracked.append(filename)
                else:
                    real_changes.append(filename)

        is_dirty = len(real_changes) > 0 or len(real_untracked) > 0
        untracked_count = len(real_untracked)

        # 4. Last commit
        last_commit = None
        log_res = subprocess.run(
            ["git", "log", "-1", "--format=%H|%s|%an|%ct"],
            cwd=repo_path, capture_output=True, text=True, env=env
        )
        if log_res.returncode == 0 and log_res.stdout.strip():
            log_parts = log_res.stdout.strip().split("|")
            if len(log_parts) == 4:
                c_hash, c_msg, c_author, c_time = log_parts
                try:
                    c_date = datetime.fromtimestamp(int(c_time), tz=timezone.utc).strftime('%Y-%m-%d %H:%M %Z')
                except Exception:
                    c_date = ""
                last_commit = {
                    "hash": c_hash[:7],
                    "message": c_msg[:80],
                    "author": c_author,
                    "date": c_date
                }

        return {
            "is_git_repo": True,
            "remote_url": remote_url,
            "current_branch": current_branch,
            "is_dirty": is_dirty,
            "untracked_count": untracked_count,
            "last_commit": last_commit
        }
    except Exception as e:
        return {"is_git_repo": False, "error": str(e)}


def get_git_info() -> Dict[str, Any]:
    """Get git info for base directory."""
    repo_path = files.get_base_dir()
    status = get_repo_status(repo_path)
    if not status.get("is_git_repo"):
        raise ValueError(status.get("error") or f"Repository at {repo_path} is not usable.")

    last_c = status.get("last_commit") or {}
    return {
        "branch": status.get("current_branch", ""),
        "commit_hash": last_c.get("hash", ""),
        "commit_time": last_c.get("date", ""),
        "tag": "",
        "short_tag": "",
        "version": last_c.get("hash", ""),
    }


def get_version() -> str:
    """Get version string of current repository."""
    try:
        git_info = get_git_info()
        return str(git_info.get("commit_hash", "")).strip() or "unknown"
    except Exception:
        return "unknown"


def is_official_agent_zero_repo() -> bool:
    """Return True when origin points to agent0ai/agent-zero or frdel/agent-zero."""
    try:
        status = get_repo_status(files.get_base_dir())
        remote_url = status.get("remote_url", "").lower().rstrip("/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        allowed_repos = ["agent0ai/agent-zero", "frdel/agent-zero"]
        return any(remote_url.endswith(r) for r in allowed_repos)
    except Exception:
        return False


def get_remote_releases(author: str, repo: str) -> GitRemoteReleasesResult:
    """Query remote Git tags/releases via git ls-remote."""
    try:
        author = author.strip()
        repo = repo.strip()
        if not author or not repo:
            return GitRemoteReleasesResult(
                is_remote=False, is_git_repo=False, author=author, repo=repo, releases=[], error="Both author and repo are required."
            )

        remote_url = f"https://github.com/{author}/{repo}.git"
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'

        res = subprocess.run(["git", "ls-remote", "--tags", "--refs", remote_url], capture_output=True, text=True, env=env)
        if res.returncode != 0:
            return GitRemoteReleasesResult(
                is_remote=True, is_git_repo=False, author=author, repo=repo, releases=[], error=f"Git remote query failed: {res.stderr}"
            )

        releases: List[GitRemoteReleaseInfo] = []
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                commit_hash, ref_name = parts
                prefix = 'refs/tags/'
                if ref_name.startswith(prefix):
                    tag_name = ref_name[len(prefix):]
                    releases.append(GitRemoteReleaseInfo(
                        tag=tag_name, commit_hash=commit_hash, short_commit_hash=commit_hash[:7], released_at=""
                    ))

        releases.sort(key=lambda release: release.tag, reverse=True)
        return GitRemoteReleasesResult(
            is_git_repo=True, is_remote=True, author=author, repo=repo, releases=releases
        )
    except Exception as e:
        return GitRemoteReleasesResult(
            is_git_repo=False, is_remote=False, author=author, repo=repo, releases=[], error=str(e)
        )


def get_remote_commits_since_local(repo_path: str) -> GitRemoteCommitsInfo:
    """Calculate how many commits remote is ahead of local."""
    try:
        if not os.path.exists(repo_path) or not os.path.exists(os.path.join(repo_path, ".git")):
            return GitRemoteCommitsInfo(
                is_git_repo=False, is_remote=False, path=repo_path, branch="", remote_branch="", commits_since_local=0, last_remote_commit_at="", error="Not a git repository"
            )

        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'

        branch_res = subprocess.run(["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True, env=env)
        branch = branch_res.stdout.strip()

        # Fetch remote
        subprocess.run(["git", "fetch"], cwd=repo_path, capture_output=True, text=True, env=env)

        count_res = subprocess.run(["git", "rev-list", f"HEAD..origin/{branch}", "--count"], cwd=repo_path, capture_output=True, text=True, env=env)
        commits_ahead = int(count_res.stdout.strip()) if count_res.returncode == 0 and count_res.stdout.strip().isdigit() else 0

        return GitRemoteCommitsInfo(
            is_git_repo=True, is_remote=True, path=repo_path, branch=branch, remote_branch=f"origin/{branch}", commits_since_local=commits_ahead, last_remote_commit_at=""
        )
    except Exception as e:
        return GitRemoteCommitsInfo(
            is_git_repo=False, is_remote=False, path=repo_path, branch="", remote_branch="", commits_since_local=0, last_remote_commit_at="", error=str(e)
        )


def get_repo_release_info(repo_path: str) -> GitRepoReleaseInfo:
    """Get full repo release info."""
    status = get_repo_status(repo_path)
    if not status.get("is_git_repo"):
        return GitRepoReleaseInfo(
            is_git_repo=False, is_remote=False, path=repo_path, author="", repo="", branch="", head=None, release=None, error=status.get("error", "Not a git repo")
        )

    last_c = status.get("last_commit") or {}
    head_info = GitHeadInfo(
        hash=last_c.get("hash", ""),
        short_hash=last_c.get("hash", "")[:7],
        message=last_c.get("message", ""),
        author=last_c.get("author", ""),
        committed_at=last_c.get("date", ""),
        authored_at=last_c.get("date", "")
    )
    return GitRepoReleaseInfo(
        is_git_repo=True,
        is_remote=bool(status.get("remote_url")),
        path=repo_path,
        author="",
        repo="",
        branch=status.get("current_branch", ""),
        head=head_info,
        release=None
    )
