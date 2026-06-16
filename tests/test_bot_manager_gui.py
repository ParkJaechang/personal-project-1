import importlib.util
from pathlib import Path
import unittest


class BotManagerGuiTests(unittest.TestCase):
    def test_gui_module_exposes_safe_manager_primitives(self):
        module_path = Path("tools/bot_manager_gui.py")
        spec = importlib.util.spec_from_file_location("bot_manager_gui", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

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


if __name__ == "__main__":
    unittest.main()
