# SOOP Telegram Clip Downloader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-friendly Telegram bot service that receives SOOP User Clip URLs, downloads the original-quality MP4 where available, and reports or delivers the result through Telegram.

**Architecture:** Implement a small Python package with pure modules for URL parsing, delivery decisions, configuration, and yt-dlp command construction. Keep Telegram polling and subprocess execution in thin boundary modules so core behavior stays easy to test.

**Tech Stack:** Python 3.11+, unittest, yt-dlp, ffmpeg, Telegram Bot API over HTTP.

---

## File Structure

- `README.md`: project overview, setup, and current status for a new PC.
- `docs/HANDOFF.md`: compact context, decisions, known constraints, and continuation instructions.
- `docs/TASKS.md`: task board for the next worker.
- `.gitignore`: ignores secrets, downloads, Python caches, and local worktrees.
- `.env.example`: documents required environment variables without secrets.
- `soop_clip_downloader/url_tools.py`: extract, normalize, and validate SOOP User Clip URLs.
- `soop_clip_downloader/telegram_delivery.py`: decide whether to send a file directly, use local Bot API, or only report the saved path.
- `soop_clip_downloader/downloader.py`: build yt-dlp commands for original-quality downloads.
- `soop_clip_downloader/config.py`: load typed settings from environment variables.
- `soop_clip_downloader/app.py`: later Telegram polling orchestration.
- `tests/test_url_tools.py`: URL behavior tests.
- `tests/test_telegram_delivery.py`: file delivery decision tests.
- `tests/test_downloader.py`: yt-dlp command construction tests.

## Task 1: Repository Handoff Docs

**Files:**
- Create: `README.md`
- Create: `docs/HANDOFF.md`
- Create: `docs/TASKS.md`
- Create: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Write repo documentation**

Create the files with the current project goal, setup instructions, current branch, intended GitHub repository `ParkJaechang/personal-project-1`, and the next tasks.

- [ ] **Step 2: Review docs**

Run:

```powershell
Get-Content README.md
Get-Content docs/HANDOFF.md
Get-Content docs/TASKS.md
```

Expected: files describe the Telegram bot service, SOOP User Clip scope, and what remains.

- [ ] **Step 3: Commit**

Run:

```powershell
git add README.md docs/HANDOFF.md docs/TASKS.md .gitignore .env.example docs/superpowers/plans/2026-06-16-soop-telegram-clip-downloader-implementation.md
git commit -m "docs: add project handoff and implementation plan"
```

Expected: a commit containing only documentation and repo hygiene files.

## Task 2: URL Parsing

**Files:**
- Create: `soop_clip_downloader/__init__.py`
- Create: `soop_clip_downloader/url_tools.py`
- Create: `tests/test_url_tools.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_url_tools.py`:

```python
from soop_clip_downloader.url_tools import (
    extract_soop_user_clip_urls,
    is_supported_soop_user_clip_url,
    normalize_soop_user_clip_url,
)


def test_extracts_unique_user_clip_urls_from_message():
    text = """
    save this https://vod.sooplive.com/player/195880425
    and this one too: https://vod.sooplive.com/player/197299925?foo=bar
    duplicate https://vod.sooplive.com/player/195880425
    """

    assert extract_soop_user_clip_urls(text) == [
        "https://vod.sooplive.com/player/195880425",
        "https://vod.sooplive.com/player/197299925",
    ]


def test_rejects_catch_urls():
    assert not is_supported_soop_user_clip_url(
        "https://vod.sooplive.com/player/197121517/catch"
    )


def test_normalizes_legacy_domain_to_current_domain():
    assert (
        normalize_soop_user_clip_url("https://vod.sooplive.co.kr/player/198263283")
        == "https://vod.sooplive.com/player/198263283"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_url_tools.py -v
```

Expected: FAIL because `soop_clip_downloader.url_tools` does not exist yet.

- [ ] **Step 3: Implement minimal URL module**

Create `src/soop_clip_downloader/url_tools.py` with a regex that accepts only `/player/{number}` and strips query strings and fragments.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest discover -s tests -p test_url_tools.py -v
```

Expected: `Ran 3 tests` and `OK`.

- [ ] **Step 5: Commit**

Run:

```powershell
git add soop_clip_downloader/__init__.py soop_clip_downloader/url_tools.py tests/test_url_tools.py
git commit -m "feat: add SOOP URL parsing"
```

## Task 3: Telegram Delivery Decisions

**Files:**
- Create: `soop_clip_downloader/telegram_delivery.py`
- Create: `tests/test_telegram_delivery.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_telegram_delivery.py`:

```python
from soop_clip_downloader.telegram_delivery import choose_delivery_method


def test_uses_default_bot_api_for_small_files():
    decision = choose_delivery_method(
        file_size_bytes=25 * 1024 * 1024,
        max_default_upload_mb=50,
        local_bot_api_base_url=None,
    )

    assert decision.method == "telegram_direct"
    assert decision.reason == "file is within the default Bot API upload limit"


def test_uses_local_bot_api_for_large_files_when_configured():
    decision = choose_delivery_method(
        file_size_bytes=400 * 1024 * 1024,
        max_default_upload_mb=50,
        local_bot_api_base_url="http://127.0.0.1:8081",
    )

    assert decision.method == "telegram_local_api"
    assert decision.reason == "file exceeds default limit but local Bot API is configured"


def test_reports_saved_path_for_large_files_without_local_api():
    decision = choose_delivery_method(
        file_size_bytes=400 * 1024 * 1024,
        max_default_upload_mb=50,
        local_bot_api_base_url=None,
    )

    assert decision.method == "saved_path_only"
    assert decision.reason == "file exceeds upload limit and local Bot API is not configured"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_telegram_delivery.py -v
```

Expected: FAIL because `telegram_delivery` does not exist yet.

- [ ] **Step 3: Implement minimal delivery module**

Create `DeliveryDecision` as a frozen dataclass and implement `choose_delivery_method`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest discover -s tests -p test_telegram_delivery.py -v
```

Expected: `Ran 3 tests` and `OK`.

- [ ] **Step 5: Commit**

Run:

```powershell
git add soop_clip_downloader/telegram_delivery.py tests/test_telegram_delivery.py
git commit -m "feat: add Telegram delivery decisions"
```

## Task 4: yt-dlp Command Builder

**Files:**
- Create: `soop_clip_downloader/downloader.py`
- Create: `tests/test_downloader.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_downloader.py`:

```python
from pathlib import Path

from soop_clip_downloader.downloader import build_ytdlp_command


def test_builds_original_quality_ytdlp_command():
    command = build_ytdlp_command(
        url="https://vod.sooplive.com/player/195880425",
        download_dir=Path("downloads"),
        ytdlp_path="yt-dlp",
        ffmpeg_path="ffmpeg",
    )

    assert command[:5] == [
        "yt-dlp",
        "--ffmpeg-location",
        "ffmpeg",
        "-f",
        "hls-original/best",
    ]
    assert "--merge-output-format" in command
    assert "https://vod.sooplive.com/player/195880425" in command
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_downloader.py -v
```

Expected: FAIL because `downloader` does not exist yet.

- [ ] **Step 3: Implement command builder**

Implement `build_ytdlp_command` as a pure function that returns an argv list and uses an output template under the configured download directory.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest discover -s tests -p test_downloader.py -v
```

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 5: Commit**

Run:

```powershell
git add soop_clip_downloader/downloader.py tests/test_downloader.py
git commit -m "feat: add yt-dlp command builder"
```

## Task 5: Configuration Loader

**Files:**
- Create: `soop_clip_downloader/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Test that required Telegram settings load, paths get defaults, integer limits parse, and missing token raises a clear `ConfigError`.

- [ ] **Step 2: Implement minimal config loader**

Use `os.environ` and a `Settings` frozen dataclass. Avoid external dotenv parsing in the first version; document that users can load env vars through PowerShell or a later launcher.

- [ ] **Step 3: Run all tests**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

Run:

```powershell
git add soop_clip_downloader/config.py tests/test_config.py
git commit -m "feat: add environment configuration"
```

## Task 6: Telegram Polling Boundary

**Files:**
- Create: `soop_clip_downloader/telegram_api.py`
- Modify: `soop_clip_downloader/app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for orchestration**

Use fake Telegram and fake downloader objects to prove the app ignores unauthorized chat IDs, queues supported URLs, and reports unsupported URLs.

- [ ] **Step 2: Implement thin orchestration**

Keep real HTTP polling out of unit tests. Put network calls behind `TelegramClient`.

- [ ] **Step 3: Run all tests**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

Run:

```powershell
git add soop_clip_downloader/telegram_api.py soop_clip_downloader/app.py tests/test_app.py
git commit -m "feat: add Telegram polling orchestration"
```

## Self-Review

Spec coverage:

- User Clip URL scope: Task 2.
- Reject Catch URLs: Task 2.
- Telegram mixed delivery strategy: Task 3.
- yt-dlp original-quality preference: Task 4.
- Environment configuration: Task 5.
- Telegram polling and allowed chat security: Task 6.
- Handoff for another PC: Task 1.

Known gap after this plan:

- GitHub repository creation depends on either an exposed connector create-repository tool, an authenticated `gh` CLI, or browser-based GitHub login. The local repo should still be kept ready to push to `ParkJaechang/personal-project-1`.
- This workspace currently contains untracked files for a different project named `personal-project-2` / `soop_summary`. Do not stage those files for `Personal Project 1`.
