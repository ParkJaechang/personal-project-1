# GitHub Setup

## Intended Repository

```text
ParkJaechang/personal-project-1
```

GitHub display title requested by the user:

```text
Personal Project 1
```

## Current Blocker

This environment can access the connected GitHub account `ParkJaechang`, but the available GitHub connector tools do not include repository creation.

Local checks also found:

- `gh` is not installed.
- `winget` is not installed.
- The in-app browser reaches GitHub login, not an authenticated session.
- `git ls-remote origin` returns `Repository not found` for `https://github.com/ParkJaechang/personal-project-1.git`.

## Fastest Unblock

Create a new GitHub repository named:

```text
personal-project-1
```

Then make sure the Codex GitHub connector has access to that repository.

## Push Commands

From this local repo:

```powershell
git push -u origin master
git push -u origin codex/soop-telegram-downloader
```

If HTTPS Git credentials are unavailable, install and authenticate GitHub CLI:

```powershell
gh auth login
git push -u origin master
git push -u origin codex/soop-telegram-downloader
```

## Branch Meaning

- `master`: design-only baseline.
- `codex/soop-telegram-downloader`: active implementation branch with docs and initial code.
