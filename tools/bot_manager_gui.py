from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL_ROOT = PROJECT_ROOT / "tools"
MANIFEST_PATH = TOOL_ROOT / "bots.json"
BOT_SCRIPT = TOOL_ROOT / "bots.ps1"
COMMAND_TIMEOUT_SECONDS = 60


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def run_bot_command(
    command: str,
    bot: str = "soop",
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    args = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(BOT_SCRIPT),
        command,
    ]
    if command != "list":
        args.append(bot)

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=creationflags,
    )


def open_path(path: Path) -> None:
    path = path.resolve()
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    subprocess.Popen(["xdg-open", str(path)])


def format_result(command: str, result: subprocess.CompletedProcess[str]) -> str:
    parts = [f"> {command}", ""]
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(stderr)
    if not stdout and not stderr:
        parts.append(f"exit_code={result.returncode}")
    return "\n".join(parts).strip()


class BotManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Bot Manager")
        self.geometry("760x500")
        self.minsize(640, 420)

        self.manifest = load_manifest()
        self.bot_names = sorted(self.manifest.get("bots", {}).keys())
        self.bot_var = tk.StringVar(value=self.bot_names[0] if self.bot_names else "")
        self.status_var = tk.StringVar(value="Ready")
        self.buttons: list[ttk.Button] = []

        self._build_styles()
        self._build_layout()
        if self.bot_names:
            self.refresh_status()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Status.TLabel", padding=(10, 4))
        style.configure("Toolbar.TFrame", padding=12)

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Bot").grid(row=0, column=0, sticky="w")
        self.bot_select = ttk.Combobox(
            toolbar,
            textvariable=self.bot_var,
            values=self.bot_names,
            state="readonly",
            width=18,
        )
        self.bot_select.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.bot_select.bind("<<ComboboxSelected>>", lambda _event: self.refresh_status())

        display_name = self._selected_display_name()
        self.display_label = ttk.Label(toolbar, text=display_name)
        self.display_label.grid(row=1, column=1, sticky="w", padx=(0, 14))

        self.status_label = ttk.Label(toolbar, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=1, column=2, sticky="e")

        toolbar.columnconfigure(1, weight=1)

        actions = ttk.Frame(self, padding=(12, 0, 12, 10))
        actions.pack(fill=tk.X)
        for label, command in [
            ("Start", self.start_bot),
            ("Stop", self.stop_bot),
            ("Restart", self.restart_bot),
            ("Refresh", self.refresh_status),
            ("Logs", self.open_logs),
            ("Downloads", self.open_downloads),
        ]:
            button = ttk.Button(actions, text=label, command=command)
            button.pack(side=tk.LEFT, padx=(0, 8))
            if label not in {"Logs", "Downloads"}:
                self.buttons.append(button)

        output_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.output = tk.Text(
            output_frame,
            wrap=tk.WORD,
            height=16,
            font=("Consolas", 10),
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

    def _selected_bot(self) -> str:
        bot = self.bot_var.get()
        if not bot:
            raise ValueError("No bot is registered in tools/bots.json.")
        return bot

    def _selected_display_name(self) -> str:
        bot = self.bot_var.get()
        config = self.manifest.get("bots", {}).get(bot, {})
        return config.get("displayName", bot)

    def _selected_config(self) -> dict:
        return self.manifest.get("bots", {}).get(self._selected_bot(), {})

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        for button in self.buttons:
            button.configure(state=state)

    def _append_output(self, text: str) -> None:
        self.output.insert(tk.END, text + "\n\n")
        self.output.see(tk.END)

    def _run_async(self, command: str, after_status: bool = False) -> None:
        try:
            bot = self._selected_bot()
        except ValueError as error:
            messagebox.showerror("Bot Manager", str(error))
            return

        self.status_var.set(f"{command}...")
        self._set_busy(True)

        def worker() -> None:
            try:
                result = run_bot_command(command, bot)
                error: Exception | None = None
            except Exception as exc:  # pragma: no cover - surfaced in the GUI.
                result = None
                error = exc

            self.after(0, lambda: self._finish_command(command, result, error, after_status))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_command(
        self,
        command: str,
        result: subprocess.CompletedProcess[str] | None,
        error: Exception | None,
        after_status: bool,
    ) -> None:
        self._set_busy(False)
        self.display_label.configure(text=self._selected_display_name())
        if error is not None:
            self.status_var.set("error")
            self._append_output(f"> {command}\n\n{error}")
            return

        assert result is not None
        text = format_result(command, result)
        self._append_output(text)
        self._update_status_from_text(result.stdout)
        if result.returncode != 0:
            self.status_var.set("error")
            messagebox.showerror("Bot Manager", result.stderr.strip() or text)
            return
        if after_status:
            self.refresh_status()

    def _update_status_from_text(self, text: str) -> None:
        lowered = text.lower()
        if "running" in lowered:
            self.status_var.set("running")
        elif "stopped" in lowered:
            self.status_var.set("stopped")
        else:
            self.status_var.set("ready")

    def refresh_status(self) -> None:
        self._run_async("status")

    def start_bot(self) -> None:
        self._run_async("start", after_status=True)

    def stop_bot(self) -> None:
        self._run_async("stop", after_status=True)

    def restart_bot(self) -> None:
        self._run_async("restart", after_status=True)

    def open_logs(self) -> None:
        config = self._selected_config()
        log_dir = resolve_project_path(str(config.get("logDirectory", "logs")))
        log_dir.mkdir(parents=True, exist_ok=True)
        open_path(log_dir)

    def open_downloads(self) -> None:
        downloads = PROJECT_ROOT / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        open_path(downloads)


def main() -> None:
    app = BotManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
