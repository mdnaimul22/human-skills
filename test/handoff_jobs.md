# Handoff Jobs — recurring scheduler definitions (both sides)

> Create these from inside an OpenCode session (plugin tools only work
> there). One job per side. Either side may use plain schtasks/cron
> for poll-only checks, but only an `opencode run` job can do fixes.

## Windows side job (this machine, workdir `E:\human-skills`)

Say in an OpenCode session:

```
Schedule a job every 30 minutes from E:\human-skills to check the
Linux report: run `python scripts/poll-handoff.py --inbox
test/linux_compat_report.md --watch NEEDS-WINDOWS`. If it reports
NEW items, implement the Windows fixes, commit, append a dated reply
to test/windows_compat_report.md, and git push. Never edit
test/linux_compat_report.md. Prefix the job name with handoff-win.
```

## Linux side job (other machine, workdir = repo checkout)

```
Schedule a job every 30 minutes from <repo-path> to check the
Windows report: run `python3 scripts/poll-handoff.py --inbox
test/windows_compat_report.md --watch NEEDS-LINUX`. If it reports
NEW items, run the Linux verifications, commit results to
test/linux_compat_report.md, and git push. Never edit
test/windows_compat_report.md. Prefix the job name with handoff-lin.
```

## Poll-only fallback (no agent, notification only)

Windows (`schtasks`, every 30 min):

```
schtasks /Create /TN "\OpenCode\handoff-poll" /TR "python E:\human-skills\scripts\poll-handoff.py --inbox test/linux_compat_report.md --watch NEEDS-WINDOWS >> %TEMP%\handoff-poll.log 2>&1" /SC MINUTE /MO 30 /F
```

Linux (`cron`, every 30 min):

```
*/30 * * * * python3 <repo-path>/scripts/poll-handoff.py --inbox test/windows_compat_report.md --watch NEEDS-LINUX >> /tmp/handoff-poll.log 2>&1
```

## Replies (append below)
