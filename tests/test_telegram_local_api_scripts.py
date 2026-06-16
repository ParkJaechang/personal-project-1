from pathlib import Path
import unittest


class TelegramLocalApiScriptTests(unittest.TestCase):
    def test_start_script_uses_docker_local_bot_api_server(self):
        script = Path("scripts/start-telegram-local-api.ps1").read_text(encoding="utf-8")

        self.assertIn("TELEGRAM_API_ID", script)
        self.assertIn("TELEGRAM_API_HASH", script)
        self.assertIn("--local", script)
        self.assertIn("aiogram/telegram-bot-api", script)
        self.assertIn("2000 MB", script)

    def test_status_and_stop_scripts_manage_same_container(self):
        status = Path("scripts/status-telegram-local-api.ps1").read_text(encoding="utf-8")
        stop = Path("scripts/stop-telegram-local-api.ps1").read_text(encoding="utf-8")

        self.assertIn("pp1-telegram-bot-api", status)
        self.assertIn("pp1-telegram-bot-api", stop)
        self.assertIn("docker", status)
        self.assertIn("docker", stop)


if __name__ == "__main__":
    unittest.main()
