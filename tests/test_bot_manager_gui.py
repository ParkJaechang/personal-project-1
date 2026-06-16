import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


def load_gui_module():
    module_path = Path("tools/bot_manager_gui.py")
    spec = importlib.util.spec_from_file_location("bot_manager_gui", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BotManagerGuiTests(unittest.TestCase):
    def test_gui_module_exposes_safe_manager_primitives(self):
        module = load_gui_module()

        self.assertTrue(callable(module.load_manifest))
        self.assertTrue(callable(module.run_bot_command))
        self.assertTrue(callable(module.open_path))
        self.assertTrue(hasattr(module, "BotManagerApp"))
        self.assertEqual(module.load_manifest()["bots"]["soop"]["displayName"], "SOOP Telegram Clip Downloader")

    def test_desktop_launcher_uses_pythonw_and_gui_module(self):
        launcher = Path("tools/bot-manager-gui.ps1").read_text(encoding="utf-8")

        self.assertIn("pythonw.exe", launcher)
        self.assertIn("bot_manager_gui.py", launcher)
        self.assertIn("Start-Process", launcher)

    def test_shortcut_creator_targets_single_gui_entry(self):
        shortcut = Path("tools/create-bot-manager-shortcut.ps1").read_text(encoding="utf-8")

        self.assertIn("WScript.Shell", shortcut)
        self.assertIn("Bot Manager.lnk", shortcut)
        self.assertIn("bot_manager_gui.py", shortcut)

    def test_start_command_does_not_capture_long_running_service_pipes(self):
        module = load_gui_module()
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            if "status" in args:
                return subprocess.CompletedProcess(args, 0, stdout="soop running pid=123\n", stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with patch.object(module.subprocess, "run", side_effect=fake_run):
            result = module.run_bot_command("start", "soop")

        self.assertGreaterEqual(len(calls), 2)
        start_kwargs = calls[0][1]
        self.assertIs(start_kwargs["stdout"], module.subprocess.DEVNULL)
        self.assertIs(start_kwargs["stderr"], module.subprocess.DEVNULL)
        self.assertNotIn("capture_output", start_kwargs)
        self.assertIn("status", calls[-1][0])
        self.assertEqual(result.stdout, "soop running pid=123\n")


if __name__ == "__main__":
    unittest.main()
