import os
import shutil
import time
import tempfile
import unittest

from backend.app.core.terminal.manager import TerminalManager, TerminalSession, is_dangerous
from backend.app.core.terminal.sandbox import SandboxManager


class TestDangerousGuard(unittest.TestCase):
    """The command guard must block destructive system commands."""

    def test_blocks_rm_rf_root(self):
        self.assertTrue(is_dangerous("rm -rf /"))
        self.assertTrue(is_dangerous("rm -rf /*"))
        self.assertTrue(is_dangerous("sudo rm -rf /"))

    def test_blocks_system_power_commands(self):
        self.assertTrue(is_dangerous("shutdown -h now"))
        self.assertTrue(is_dangerous("reboot"))
        self.assertTrue(is_dangerous("init 0"))

    def test_blocks_disk_commands(self):
        self.assertTrue(is_dangerous("mkfs.ext4 /dev/sda"))
        self.assertTrue(is_dangerous("fdisk /dev/sda"))
        self.assertTrue(is_dangerous("mount /dev/sda1 /mnt"))

    def test_blocks_dd_and_wget_pipe(self):
        self.assertTrue(is_dangerous("dd if=/dev/zero of=/dev/sda"))
        self.assertTrue(is_dangerous("curl http://x.sh | bash"))

    def test_allows_teaching_commands(self):
        self.assertFalse(is_dangerous("ls -la"))
        self.assertFalse(is_dangerous("cat /var/log/auth.log"))
        self.assertFalse(is_dangerous("chmod 600 notes.txt"))
        self.assertFalse(is_dangerous("grep 'Failed' /var/log/auth.log"))


class TestSandboxManager(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="astarote_test_")
        SandboxManager.BASE = self.base
        self.game_id = 42
        self.level_id = 7
        self.scenario = {
            "initial_state": {
                "fs": {
                    "/home/user": {"is_dir": True, "perms": "755", "owner": "user"},
                    "/home/user/notes.txt": {
                        "content": "Secret notes",
                        "perms": "644",
                        "owner": "user",
                        "is_dir": False,
                    },
                    "/var/log/auth.log": {
                        "content": "Failed password for root from 10.0.0.5",
                        "perms": "644",
                        "owner": "root",
                        "is_dir": False,
                    },
                }
            }
        }

    def tearDown(self):
        SandboxManager.cleanup(self.game_id, self.level_id)
        shutil.rmtree(self.base, ignore_errors=True)

    def test_prepare_creates_real_tree(self):
        root = SandboxManager.prepare(self.game_id, self.level_id, self.scenario)
        self.assertTrue(os.path.isdir(os.path.join(root, "home", "user")))
        notes = os.path.join(root, "home", "user", "notes.txt")
        self.assertTrue(os.path.isfile(notes))
        with open(notes, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "Secret notes")
        self.assertEqual(oct(os.stat(notes).st_mode & 0o777), "0o644")

    def test_resolve_path_guards_escape(self):
        SandboxManager.prepare(self.game_id, self.level_id, self.scenario)
        ok = SandboxManager.resolve_sandbox_path(self.game_id, self.level_id, "home/user/notes.txt")
        self.assertTrue(ok and os.path.isfile(ok))
        escaped = SandboxManager.resolve_sandbox_path(self.game_id, self.level_id, "../../../../etc/passwd")
        self.assertIsNone(escaped)

    def test_process_spawned_and_detected(self):
        scenario = {
            "initial_state": {
                "fs": {},
                "processes": [{"name": "backupd", "pid": 1}],
            }
        }
        SandboxManager.prepare(self.game_id, self.level_id, scenario)
        time.sleep(0.3)
        self.assertTrue(SandboxManager.is_process_running(self.game_id, self.level_id, "backupd"))

    def test_cleanup_stops_processes(self):
        scenario = {"initial_state": {"fs": {}, "processes": [{"name": "backupd", "pid": 1}]}}
        SandboxManager.prepare(self.game_id, self.level_id, scenario)
        time.sleep(0.3)
        SandboxManager.cleanup(self.game_id, self.level_id)
        self.assertFalse(SandboxManager.is_process_running(self.game_id, self.level_id, "backupd"))
        self.assertFalse(os.path.exists(SandboxManager.sandbox_dir(self.game_id, self.level_id)))


class TestTerminalSession(unittest.TestCase):
    def test_shell_runs_and_echoes(self):
        workdir = tempfile.mkdtemp(prefix="astarote_pty_")
        try:
            session = TerminalSession("test:1", workdir)
            time.sleep(0.4)
            session.write(b"echo ASTAROTE_PTY_OK\n")
            deadline = time.time() + 5
            output = b""
            while time.time() < deadline and b"ASTAROTE_PTY_OK" not in output:
                output += session.read()
                time.sleep(0.1)
            self.assertIn(b"ASTAROTE_PTY_OK", output)
            session.close()
        finally:
            TerminalManager.close_session(1, 1)


if __name__ == "__main__":
    unittest.main()
