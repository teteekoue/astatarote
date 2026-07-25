import unittest
from backend.app.core.terminal.manager import TerminalSimulator

class TestTerminalSimulator(unittest.TestCase):
    def setUp(self):
        # Create a clean initial state before each test
        self.state = {
            "cwd": "/home/user",
            "fs": {
                "/home/user": {"is_dir": True, "perms": "755", "owner": "user"},
                "/home/user/notes.txt": {
                    "content": "Secret notes",
                    "perms": "644",
                    "owner": "user",
                    "is_dir": False
                }
            },
            "processes": [
                {"pid": 1, "name": "systemd", "ppid": 0}
            ]
        }

    def test_pwd(self):
        stdout, new_state = TerminalSimulator.execute("pwd", self.state)
        self.assertEqual(stdout, "/home/user")
        self.assertEqual(new_state["cwd"], "/home/user")

    def test_whoami(self):
        stdout, _ = TerminalSimulator.execute("whoami", self.state)
        self.assertEqual(stdout, "user")

    def test_cd_valid(self):
        # Add parent folder to simulate cd
        self.state["fs"]["/home"] = {"is_dir": True, "perms": "755", "owner": "root"}
        stdout, new_state = TerminalSimulator.execute("cd /home", self.state)
        self.assertEqual(stdout, "")
        self.assertEqual(new_state["cwd"], "/home")

    def test_cd_invalid(self):
        stdout, new_state = TerminalSimulator.execute("cd /invalid_dir", self.state)
        self.assertIn("Aucun fichier ou dossier", stdout)
        self.assertEqual(new_state["cwd"], "/home/user")

    def test_cat_valid(self):
        stdout, _ = TerminalSimulator.execute("cat notes.txt", self.state)
        self.assertEqual(stdout, "Secret notes")

    def test_touch(self):
        stdout, new_state = TerminalSimulator.execute("touch new_file.txt", self.state)
        self.assertEqual(stdout, "")
        self.assertIn("/home/user/new_file.txt", new_state["fs"])
        self.assertEqual(new_state["fs"]["/home/user/new_file.txt"]["perms"], "644")

    def test_redirection_write(self):
        # echo "hello" > hello.txt
        stdout, new_state = TerminalSimulator.execute("echo 'hello' > hello.txt", self.state)
        self.assertEqual(stdout, "")
        self.assertIn("/home/user/hello.txt", new_state["fs"])
        self.assertEqual(new_state["fs"]["/home/user/hello.txt"]["content"].strip(), "hello")

    def test_chmod(self):
        stdout, new_state = TerminalSimulator.execute("chmod 600 notes.txt", self.state)
        self.assertEqual(stdout, "")
        self.assertEqual(new_state["fs"]["/home/user/notes.txt"]["perms"], "600")

    def test_forbidden_command(self):
        stdout, _ = TerminalSimulator.execute("rm -rf /", self.state)
        self.assertIn("Commande interdite", stdout)

if __name__ == "__main__":
    unittest.main()
