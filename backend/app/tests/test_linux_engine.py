"""
Deterministic Linux engine — test suite.

These tests replay a full learner walkthrough of every level of the frozen
"Linux Essentials" course: they double as (1) engine regression tests and
(2) proof that each hand-crafted challenge is actually solvable with the
commands the engine provides, and that the validation checks pass.
"""
import unittest

from backend.app.catalog import get_game
from backend.app.core.terminal.engine.shell import DeterministicShell


GAME = get_game("linux-essentials")


def new_shell(level_index: int) -> DeterministicShell:
    return DeterministicShell(scenario=GAME["levels"][level_index]["scenario"])


class TestBasicCommands(unittest.TestCase):
    def setUp(self):
        self.shell = new_shell(0)

    def test_prompt_and_pwd(self):
        result = self.shell.execute("pwd")
        self.assertEqual(result.output.strip(), "/home/user")
        self.assertEqual(result.status, 0)

    def test_ls_lists_home(self):
        result = self.shell.execute("ls")
        self.assertIn("readme.md", result.output)
        self.assertIn("Documents", result.output)

    def test_ls_relative_path(self):
        result = self.shell.execute("ls Documents")
        self.assertIn("planning_equipe.txt", result.output)

    def test_cat_file(self):
        result = self.shell.execute("cat readme.md")
        self.assertIn("Bienvenue", result.output)

    def test_unknown_command(self):
        result = self.shell.execute("frobnicate")
        self.assertIn("command not found", result.output)
        self.assertEqual(result.status, 127)

    def test_missing_file_error(self):
        result = self.shell.execute("cat inexistent.txt")
        self.assertIn("No such file or directory", result.output)
        self.assertEqual(result.status, 1)

    def test_determinism_same_output(self):
        a = new_shell(0).execute("ls -l").output
        b = new_shell(0).execute("ls -l").output
        self.assertEqual(a, b)


class TestPipesAndRedirects(unittest.TestCase):
    def setUp(self):
        self.shell = new_shell(2)  # log analysis level

    def test_grep_counts_failures(self):
        result = self.shell.execute("grep -c 'Failed password' /var/log/auth.log")
        self.assertEqual(result.output.strip(), "9")

    def test_pipe_to_wc(self):
        result = self.shell.execute("grep 'Failed password' /var/log/auth.log | wc -l")
        self.assertIn("9", result.output)

    def test_head_and_tail(self):
        self.assertIn("Jan  1 06:12:03", self.shell.execute("head -n 1 /var/log/auth.log").output)
        self.assertIn("Daily apt", self.shell.execute("tail -n 1 /var/log/auth.log").output)

    def test_redirect_creates_file(self):
        self.shell.execute("mkdir audit")
        self.shell.execute("echo 9 > audit/echecs.txt")
        node = self.shell.vfs.get("/home/user/audit/echecs.txt")
        self.assertIsNotNone(node)
        self.assertEqual(node.content.strip(), "9")

    def test_append_redirect(self):
        self.shell.execute("echo a > /tmp/f.txt")
        self.shell.execute("echo b >> /tmp/f.txt")
        node = self.shell.vfs.get("/tmp/f.txt")
        self.assertIn("a", node.content)
        self.assertIn("b", node.content)


class TestLevel2FindAndExtract(unittest.TestCase):
    """Full solution walkthrough of level 2."""

    def test_solution(self):
        shell = new_shell(1)
        find = shell.execute('find /etc -name "backup.conf"')
        self.assertIn("/etc/meridian/backup.conf", find.output)

        cat = shell.execute("cat /etc/meridian/backup.conf")
        self.assertIn("API_KEY=MERIDIAN-7F3K-2026", cat.output)

        shell.execute('echo "MERIDIAN-7F3K-2026" > /home/user/verification.txt')
        node = shell.vfs.get("/home/user/verification.txt")
        self.assertIn("MERIDIAN-7F3K-2026", node.content)

        # expected_state checks
        expected = GAME["levels"][1]["expected_state"]
        check = expected["files_checks"][0]
        self.assertIn(check["content_contains"].lower(), node.content.lower())
        self.assertTrue(any("find" in h for h in shell.history))


class TestLevel4FileOperations(unittest.TestCase):
    def test_solution(self):
        shell = new_shell(3)
        shell.execute("mkdir archive")
        shell.execute("mv projects/brouillon.txt archive/")
        shell.execute("mv projects/ancien_projet archive/")
        shell.execute("cp projects/TODO.txt Documents/")
        shell.execute("rm projects/test_temp.log")
        shell.execute("touch archive/lisez_moi.txt")

        self.assertIsNotNone(shell.vfs.get("/home/user/archive/brouillon.txt"))
        self.assertIsNotNone(shell.vfs.get("/home/user/archive/ancien_projet"))
        self.assertEqual(shell.vfs.get("/home/user/archive/ancien_projet").kind, "dir")
        self.assertIsNotNone(shell.vfs.get("/home/user/Documents/TODO.txt"))
        self.assertIsNotNone(shell.vfs.get("/home/user/archive/lisez_moi.txt"))
        self.assertIsNone(shell.vfs.get("/home/user/projects/brouillon.txt"))
        self.assertIsNone(shell.vfs.get("/home/user/projects/test_temp.log"))
        # original TODO kept in projects
        self.assertIsNotNone(shell.vfs.get("/home/user/projects/TODO.txt"))

    def test_rm_dir_requires_r(self):
        shell = new_shell(3)
        result = shell.execute("rm projects/ancien_projet")
        self.assertIn("Is a directory", result.output)


class TestLevel5Permissions(unittest.TestCase):
    def test_solution(self):
        shell = new_shell(4)
        shell.execute("ls -l vault")
        shell.execute("chmod 600 vault/rapport_salaire.txt")
        shell.execute("chmod 750 vault/script_deploiement.sh")
        shell.execute("chmod 644 vault/public/annonce.txt")

        self.assertEqual(oct(shell.vfs.get("/home/user/vault/rapport_salaire.txt").perms), "0o600")
        self.assertEqual(oct(shell.vfs.get("/home/user/vault/script_deploiement.sh").perms), "0o750")
        self.assertEqual(oct(shell.vfs.get("/home/user/vault/public/annonce.txt").perms), "0o644")

    def test_symbolic_chmod(self):
        shell = new_shell(4)
        shell.execute("chmod u+x,go-rwx vault/rapport_salaire.txt")
        self.assertEqual(shell.vfs.get("/home/user/vault/rapport_salaire.txt").perms, 0o700)

    def test_stat_shows_permissions(self):
        shell = new_shell(4)
        shell.execute("chmod 600 vault/rapport_salaire.txt")
        result = shell.execute("stat vault/rapport_salaire.txt")
        self.assertIn("(0600/-rw-------)", result.output)


class TestLevel6Sudo(unittest.TestCase):
    def test_permission_denied_without_sudo(self):
        shell = new_shell(5)
        result = shell.execute("cat /root/rapport_confidentiel.txt")
        self.assertIn("Permission denied", result.output)
        self.assertEqual(result.status, 1)

    def test_solution_with_sudo(self):
        shell = new_shell(5)
        shell.execute("id")
        result = shell.execute("sudo cat /root/rapport_confidentiel.txt")
        self.assertIn("AUTH-MASTER-92X", result.output)

        shell.execute("mkdir -p audit")
        shell.execute('echo "AUTH-MASTER-92X" > audit/decouverte.txt')
        node = shell.vfs.get("/home/user/audit/decouverte.txt")
        self.assertIn("AUTH-MASTER-92X", node.content)
        self.assertTrue(any("sudo" in h for h in shell.history))

    def test_etc_passwd_readable(self):
        shell = new_shell(5)
        result = shell.execute("cat /etc/passwd")
        self.assertIn("user:x:1000", result.output)


class TestLevel7Processes(unittest.TestCase):
    def test_ps_aux_shows_scenario_processes(self):
        shell = new_shell(6)
        result = shell.execute("ps aux")
        self.assertIn("backup_loop", result.output)
        self.assertIn("restore_daemon", result.output)
        self.assertIn("97.3", result.output)

    def test_grep_pipe_filters(self):
        shell = new_shell(6)
        result = shell.execute("ps aux | grep backup")
        self.assertIn("backup_loop", result.output)

    def test_solution_kill_backup_loop_only(self):
        shell = new_shell(6)
        shell.execute("ps aux")
        # scenario gives backup_loop pid 1244
        shell.execute("kill 1244")

        self.assertIsNone(shell.processes.find(name="backup_loop"))
        self.assertIsNotNone(shell.processes.find(name="restore_daemon"))

    def test_cannot_kill_root_process(self):
        shell = new_shell(6)
        proc = shell.processes.find(name="meridian-indexer")
        self.assertIsNotNone(proc)
        result = shell.execute(f"kill {proc.pid}")
        self.assertIn("Operation not permitted", result.output)
        self.assertIsNotNone(shell.processes.find(name="meridian-indexer"))

    def test_kill_unknown_pid(self):
        shell = new_shell(6)
        result = shell.execute("kill 99999")
        self.assertIn("No such process", result.output)


class TestLevel8Incident(unittest.TestCase):
    def test_solution_walkthrough(self):
        shell = new_shell(7)

        # 1. locate
        find = shell.execute('find /var/tmp -name "*.sh"')
        self.assertIn("/var/tmp/.hidden_service/backdoor.sh", find.output)

        # 2. read
        cat = shell.execute("cat /var/tmp/.hidden_service/backdoor.sh")
        self.assertIn("203.0.113.66", cat.output)

        # 3. kill
        proc = shell.processes.find(name="backdoor.sh")
        self.assertIsNotNone(proc)
        shell.execute(f"kill -9 {proc.pid}")
        self.assertIsNone(shell.processes.find(name="backdoor.sh"))

        # 4-6. quarantine + lock
        shell.execute("mkdir quarantine")
        shell.execute("mv /var/tmp/.hidden_service/backdoor.sh quarantine/")
        shell.execute("chmod 000 quarantine/backdoor.sh")

        self.assertIsNone(shell.vfs.get("/var/tmp/.hidden_service/backdoor.sh"))
        node = shell.vfs.get("/home/user/quarantine/backdoor.sh")
        self.assertIsNotNone(node)
        self.assertEqual(node.perms, 0)

        # 7. report
        shell.execute(
            'echo "Backdoor neutralisee : IP 203.0.113.66, fichier isole en quarantine" '
            '> rapport_incident.txt'
        )
        report = shell.vfs.get("/home/user/rapport_incident.txt")
        self.assertIn("backdoor", report.content.lower())
        self.assertIn("203.0.113.66", report.content)

        # all expected_state checks pass
        expected = GAME["levels"][7]["expected_state"]
        for check in expected["files_checks"]:
            n = shell.vfs.get(check["path"])
            self.assertIsNotNone(n, check["path"])
            if "perms" in check:
                self.assertEqual(oct(n.perms)[2:].zfill(3), check["perms"])
            if "content_contains" in check:
                self.assertIn(check["content_contains"].lower(), n.content.lower())
        for check in expected["files_not_exists"]:
            self.assertIsNone(shell.vfs.get(check["path"]), check["path"])


class TestPersistenceRoundTrip(unittest.TestCase):
    def test_state_survives_serialization(self):
        shell = new_shell(3)
        shell.execute("mkdir archive")
        shell.execute("echo 'important' > archive/note.txt")
        shell.execute("chmod 640 archive/note.txt")

        data = shell.to_dict()
        restored = DeterministicShell.from_dict(data, scenario=GAME["levels"][3]["scenario"])

        self.assertEqual(restored.cwd, shell.cwd)
        node = restored.vfs.get("/home/user/archive/note.txt")
        self.assertIsNotNone(node)
        self.assertEqual(node.content.strip(), "important")
        self.assertEqual(node.perms, 0o640)
        self.assertIn("mkdir archive", restored.history)


class TestResponseHooks(unittest.TestCase):
    def test_scripted_response_exact_match(self):
        shell = new_shell(6)
        result = shell.execute("systemctl status backup_loop")
        self.assertIn("backup_loop.service", result.output)
        self.assertIn("1244", result.output)

    def test_ss_hook_level8(self):
        shell = new_shell(7)
        result = shell.execute("ss -tulpn")
        self.assertIn("203.0.113.66:4444", result.output)


class TestCompletion(unittest.TestCase):
    def test_command_completion(self):
        shell = new_shell(0)
        result = shell.complete("gre")
        self.assertIn("grep", result["candidates"])

    def test_path_completion(self):
        shell = new_shell(0)
        result = shell.complete("ls Doc")
        self.assertIn("Documents/", result["candidates"])


class TestSafetyGuards(unittest.TestCase):
    def test_rm_rf_root_blocked(self):
        shell = new_shell(0)
        result = shell.execute("rm -rf /")
        self.assertIn("dangerous", result.output)
        self.assertIsNotNone(shell.vfs.get("/home/user"))

    def test_power_commands_disabled(self):
        shell = new_shell(0)
        result = shell.execute("reboot")
        self.assertIn("désactivées", result.output)


if __name__ == "__main__":
    unittest.main()
