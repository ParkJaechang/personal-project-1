from pathlib import Path
import json
import unittest


class BotManagerTests(unittest.TestCase):
    def test_manifest_registers_soop_bot(self):
        manifest = json.loads(Path("tools/bots.json").read_text(encoding="utf-8"))

        self.assertIn("soop", manifest["bots"])
        soop = manifest["bots"]["soop"]
        self.assertEqual(soop["displayName"], "Clip")
        self.assertEqual(soop["workingDirectory"], ".")
        self.assertEqual(soop["startScript"], "scripts/run-service.ps1")
        self.assertEqual(soop["processMatch"], "soop_clip_downloader")

    def test_manifest_registers_telegram_local_api(self):
        manifest = json.loads(Path("tools/bots.json").read_text(encoding="utf-8"))

        self.assertIn("telegram-local-api", manifest["bots"])
        local_api = manifest["bots"]["telegram-local-api"]
        self.assertEqual(local_api["displayName"], "telegram local api")
        self.assertEqual(local_api["startMode"], "script")
        self.assertEqual(local_api["startScript"], "scripts/start-telegram-local-api.ps1")
        self.assertEqual(local_api["statusScript"], "scripts/status-telegram-local-api.ps1")
        self.assertEqual(local_api["stopScript"], "scripts/stop-telegram-local-api.ps1")

    def test_manager_exposes_expected_commands(self):
        script = Path("tools/bots.ps1").read_text(encoding="utf-8")

        for command in [
            "status",
            "start",
            "stop",
            "restart",
            "logs",
            "list",
        ]:
            self.assertIn(command, script)

        self.assertIn("bots.json", script)
        self.assertIn("Start-Process", script)
        self.assertIn("Get-CimInstance Win32_Process", script)
        self.assertIn("Stop-Process", script)
        self.assertIn("statusScript", script)
        self.assertIn("stopScript", script)
        self.assertIn("startMode", script)


if __name__ == "__main__":
    unittest.main()
