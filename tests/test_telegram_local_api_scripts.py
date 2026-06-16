from pathlib import Path
import unittest


class TelegramLocalApiScriptTests(unittest.TestCase):
    def test_start_script_uses_docker_local_bot_api_server(self):
        script = Path("scripts/start-telegram-local-api.ps1").read_text(encoding="utf-8")

        self.assertIn("TELEGRAM_API_ID", script)
        self.assertIn("TELEGRAM_API_HASH", script)
        self.assertIn("TELEGRAM_LOCAL=1", script)
        self.assertIn("TELEGRAM_HTTP_IP_ADDRESS=0.0.0.0", script)
        self.assertIn("aiogram/telegram-bot-api", script)
        self.assertIn("pp1-telegram-bot-api-data", script)
        self.assertIn("/telegram-files:ro", script)
        self.assertIn("2000 MB", script)
        self.assertIn("Resolve-DockerCommand", script)
        self.assertIn("Invoke-DockerText", script)
        self.assertIn("LASTEXITCODE", script)
        self.assertIn("C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe", script)

    def test_status_and_stop_scripts_manage_same_container(self):
        status = Path("scripts/status-telegram-local-api.ps1").read_text(encoding="utf-8")
        stop = Path("scripts/stop-telegram-local-api.ps1").read_text(encoding="utf-8")

        self.assertIn("pp1-telegram-bot-api", status)
        self.assertIn("pp1-telegram-bot-api", stop)
        self.assertIn("docker", status)
        self.assertIn("docker", stop)
        self.assertIn("Resolve-DockerCommand", status)
        self.assertIn("Resolve-DockerCommand", stop)
        self.assertIn("Wait-Job", status)
        self.assertIn("Docker engine not running", status)
        self.assertIn("Docker engine not running", stop)

    def test_wsl_prerequisite_script_enables_required_windows_features(self):
        script = Path("scripts/enable-wsl-for-docker.ps1").read_text(encoding="utf-8")

        self.assertIn("Microsoft-Windows-Subsystem-Linux", script)
        self.assertIn("VirtualMachinePlatform", script)
        self.assertIn("wsl.exe --install --no-distribution", script)


if __name__ == "__main__":
    unittest.main()
