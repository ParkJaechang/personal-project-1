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
APP_NAME = "app manager"

STATUS_COLORS = {
    "running": ("#107c41", "#ffffff"),
    "stopped": ("#8a2f0b", "#ffffff"),
    "ready": ("#5f6368", "#ffffff"),
    "error": ("#b3261e", "#ffffff"),
}


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
    args = build_bot_command_args(command, bot)

    if command in {"start", "restart"}:
        result = run_bot_process(args, timeout=timeout, capture=False)
        if result.returncode != 0:
            return result
        return run_bot_process(build_bot_command_args("status", bot), timeout=timeout, capture=True)

    return run_bot_process(args, timeout=timeout, capture=True)


def build_bot_command_args(command: str, bot: str = "soop") -> list[str]:
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

    return args


def run_bot_process(
    args: list[str],
    timeout: int,
    capture: bool,
) -> subprocess.CompletedProcess[str]:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    io_options: dict[str, object]
    if capture:
        io_options = {"capture_output": True}
    else:
        io_options = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=creationflags,
        **io_options,
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


def status_kind_from_text(text: str) -> str:
    lowered = text.lower()
    if "running" in lowered:
        return "running"
    if "stopped" in lowered:
        return "stopped"
    return "ready"


def status_text(kind: str) -> str:
    return {
        "running": "Running",
        "stopped": "Stopped",
        "ready": "Ready",
        "error": "Error",
    }.get(kind, "Ready")


class BotManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("840x540")
        self.minsize(760, 460)

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
        style.configure(".", font=("Segoe UI", 9))
        style.configure("Root.TFrame", background="#f5f5f5")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 17), background="#ffffff")
        style.configure("AppTitle.TLabel", font=("Segoe UI Semibold", 16), background="#ffffff")
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 10), background="#ffffff")
        style.configure("Muted.TLabel", foreground="#666666", background="#ffffff")
        style.configure("Panel.TButton", padding=(14, 7))
        style.configure("Primary.TButton", padding=(14, 7))

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12, style="Root.TFrame")
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root, padding=(14, 12), style="Panel.TFrame")
        header.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            header,
            text="Start, stop, and inspect local services",
            style="Muted.TLabel",
        ).pack(side=tk.LEFT, padx=(12, 0))

        main = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        nav = ttk.Frame(main, padding=12, style="Panel.TFrame")
        main.add(nav, weight=0)
        ttk.Label(nav, text="Apps", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.app_list = tk.Listbox(
            nav,
            activestyle="none",
            borderwidth=0,
            exportselection=False,
            font=("Segoe UI", 10),
            height=8,
            highlightthickness=1,
            relief=tk.FLAT,
            selectbackground="#dbeafe",
            selectforeground="#111111",
            width=24,
        )
        for bot in self.bot_names:
            self.app_list.insert(tk.END, self._display_name_for_bot(bot))
        self.app_list.pack(fill=tk.X)
        if self.bot_names:
            self.app_list.selection_set(0)
        self.app_list.bind("<<ListboxSelect>>", self._on_app_selected)

        ttk.Label(
            nav,
            text="Select an app, then use the controls on the right.",
            style="Muted.TLabel",
            wraplength=180,
        ).pack(anchor="w", pady=(14, 0))

        detail = ttk.Frame(main, padding=14, style="Panel.TFrame")
        main.add(detail, weight=1)

        title_row = ttk.Frame(detail, style="Panel.TFrame")
        title_row.pack(fill=tk.X)
        self.display_label = ttk.Label(
            title_row,
            text=self._selected_display_name(),
            style="AppTitle.TLabel",
        )
        self.display_label.pack(side=tk.LEFT)
        self.status_badge = tk.Label(
            title_row,
            textvariable=self.status_var,
            padx=12,
            pady=4,
            borderwidth=0,
            font=("Segoe UI Semibold", 9),
        )
        self.status_badge.pack(side=tk.RIGHT)
        self._set_status("ready")

        controls = ttk.Frame(detail, padding=(0, 16, 0, 8), style="Panel.TFrame")
        controls.pack(fill=tk.X)
        for label, command in [
            ("Start", self.start_bot),
            ("Stop", self.stop_bot),
            ("Restart", self.restart_bot),
            ("Refresh", self.refresh_status),
        ]:
            button = ttk.Button(controls, text=label, command=command, style="Panel.TButton")
            button.pack(side=tk.LEFT, padx=(0, 8))
            self.buttons.append(button)

        tools = ttk.Frame(detail, padding=(0, 0, 0, 14), style="Panel.TFrame")
        tools.pack(fill=tk.X)
        for label, command in [
            ("Logs", self.open_logs),
            ("Downloads", self.open_downloads),
        ]:
            button = ttk.Button(tools, text=label, command=command, style="Panel.TButton")
            button.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(detail, text="Activity", style="Section.TLabel").pack(anchor="w", pady=(4, 8))
        output_frame = ttk.Frame(detail, style="Panel.TFrame")
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.output = tk.Text(
            output_frame,
            wrap=tk.WORD,
            height=16,
            font=("Consolas", 10),
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=8,
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

    def _display_name_for_bot(self, bot: str) -> str:
        config = self.manifest.get("bots", {}).get(bot, {})
        return config.get("displayName", bot)

    def _on_app_selected(self, _event=None) -> None:
        selection = self.app_list.curselection()
        if not selection:
            return
        self.bot_var.set(self.bot_names[selection[0]])
        self.display_label.configure(text=self._selected_display_name())
        self._set_status("ready")
        self.refresh_status()

    def _selected_bot(self) -> str:
        bot = self.bot_var.get()
        if not bot:
            raise ValueError("No bot is registered in tools/bots.json.")
        return bot

    def _selected_display_name(self) -> str:
        return self._display_name_for_bot(self.bot_var.get())

    def _selected_config(self) -> dict:
        return self.manifest.get("bots", {}).get(self._selected_bot(), {})

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        for button in self.buttons:
            button.configure(state=state)

    def _append_output(self, text: str) -> None:
        self.output.insert(tk.END, text + "\n\n")
        self.output.see(tk.END)

    def _set_status(self, kind: str, label: str | None = None) -> None:
        self.status_var.set(label or status_text(kind))
        background, foreground = STATUS_COLORS.get(kind, STATUS_COLORS["ready"])
        if hasattr(self, "status_badge"):
            self.status_badge.configure(background=background, foreground=foreground)

    def _run_async(self, command: str, after_status: bool = False) -> None:
        try:
            bot = self._selected_bot()
        except ValueError as error:
            messagebox.showerror(APP_NAME, str(error))
            return

        self._set_status("ready", f"{command}...")
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
            self._set_status("error")
            self._append_output(f"> {command}\n\n{error}")
            return

        assert result is not None
        text = format_result(command, result)
        self._append_output(text)
        self._update_status_from_text(result.stdout)
        if result.returncode != 0:
            self._set_status("error")
            messagebox.showerror(APP_NAME, result.stderr.strip() or text)
            return
        if after_status:
            self.refresh_status()

    def _update_status_from_text(self, text: str) -> None:
        self._set_status(status_kind_from_text(text))

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
