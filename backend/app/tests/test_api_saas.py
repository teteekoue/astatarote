"""
API-level tests: SaaS flow — register, browse the catalog, enroll,
run commands through the terminal websocket handler and validate levels.
"""
import os
import tempfile
import unittest

# A shared on-disk temp DB: TestClient runs the app in another thread, and
# in-memory SQLite would give each thread its own database.
_TMP_DB = tempfile.mktemp(prefix="astarote_test_", suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402
from backend.app.core.database.session import Base, engine, SessionLocal  # noqa: E402
from backend.app.models.models import Game, GameState, Level, User  # noqa: E402

Base.metadata.create_all(bind=engine)


class TestSaasFlow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.suffix = os.urandom(4).hex()
        self.username = f"learner_{self.suffix}"
        r = self.client.post("/api/auth/register", json={
            "username": self.username,
            "email": f"{self.username}@test.dev",
            "password": "motdepasse123",
        })
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post("/api/auth/login", json={
            "username": self.username, "password": "motdepasse123",
        })
        self.token = r.json()["access_token"]
        self.auth = {"Authorization": f"Bearer {self.token}"}

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["version"], "3.0.0")

    def test_catalog_listing_and_enrollment(self):
        r = self.client.get("/api/catalog", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        catalog = r.json()
        self.assertTrue(any(g["slug"] == "linux-essentials" for g in catalog))
        game_meta = next(g for g in catalog if g["slug"] == "linux-essentials")
        self.assertEqual(game_meta["total_levels"], 8)

        r = self.client.post("/api/games", headers=self.auth,
                             json={"catalog_slug": "linux-essentials"})
        self.assertEqual(r.status_code, 200, r.text)
        game = r.json()
        self.assertEqual(game["total_levels"], 8)
        game_id = game["id"]

        # Levels are copies of the frozen catalog content
        r = self.client.get(f"/api/games/{game_id}/levels", headers=self.auth)
        levels = r.json()
        self.assertEqual(len(levels), 8)
        self.assertEqual(levels[0]["status"], "available")
        self.assertEqual(levels[1]["status"], "locked")
        self.assertIn("répertoire de travail", levels[0]["consigne"])

    def test_enrollment_is_idempotent(self):
        g1 = self.client.post("/api/games", headers=self.auth,
                              json={"catalog_slug": "linux-essentials"}).json()
        g2 = self.client.post("/api/games", headers=self.auth,
                              json={"catalog_slug": "linux-essentials"}).json()
        self.assertEqual(g1["id"], g2["id"])

    def test_full_level1_via_terminal_websocket(self):
        game = self.client.post("/api/games", headers=self.auth,
                                json={"catalog_slug": "linux-essentials"}).json()
        game_id = game["id"]

        with self.client.websocket_connect(
            f"/ws/terminal/{game_id}?level=0&token={self.token}"
        ) as ws:
            def run(line):
                """Send a command; return its output (consumes the trailing prompt)."""
                ws.send_json({"type": "input", "line": line})
                out = ws.receive_json()
                prompt = ws.receive_json()
                assert "user@meridian" in prompt["output"]
                return out["output"]

            banner = ws.receive_json()
            self.assertEqual(banner["type"], "banner")

            prompt = ws.receive_json()
            self.assertIn("user@meridian", prompt["output"])

            self.assertIn("/home/user", run("pwd"))
            self.assertIn("readme.md", run("ls"))

            ws.send_json({"type": "complete", "line": "gre"})
            completion = ws.receive_json()
            self.assertIn("grep", completion["candidates"])

        # Validate level 1 — commands_used: pwd + ls were run
        r = self.client.post(f"/api/games/{game_id}/levels/0/validate",
                             headers=self.auth)
        result = r.json()
        self.assertTrue(result["success"], result["message"])
        self.assertEqual(result["points_earned"], 100)
        self.assertEqual(result["next_level_index"], 1)

        # Level 2 unlocked
        r = self.client.get(f"/api/games/{game_id}/levels", headers=self.auth)
        self.assertEqual(r.json()[1]["status"], "available")

        # Stats updated
        r = self.client.get("/api/users/me", headers=self.auth)
        self.assertEqual(r.json()["stats"]["points"], 100)

    def test_validation_fails_without_work(self):
        game = self.client.post("/api/games", headers=self.auth,
                                json={"catalog_slug": "linux-essentials"}).json()
        game_id = game["id"]

        with self.client.websocket_connect(
            f"/ws/terminal/{game_id}?level=0&token={self.token}"
        ) as ws:
            ws.receive_json()  # banner
            ws.receive_json()  # prompt

        r = self.client.post(f"/api/games/{game_id}/levels/0/validate",
                             headers=self.auth)
        result = r.json()
        self.assertFalse(result["success"])

    def test_terminal_requires_auth(self):
        game = self.client.post("/api/games", headers=self.auth,
                                json={"catalog_slug": "linux-essentials"}).json()
        with self.client.websocket_connect(
            f"/ws/terminal/{game['id']}?level=0&token=invalid-token"
        ) as ws:
            msg = ws.receive_json()
            self.assertEqual(msg["type"], "error")

    def test_cannot_access_other_users_game(self):
        game = self.client.post("/api/games", headers=self.auth,
                                json={"catalog_slug": "linux-essentials"}).json()
        # second user
        other = f"other_{self.suffix}"
        self.client.post("/api/auth/register", json={
            "username": other, "email": f"{other}@test.dev", "password": "motdepasse123",
        })
        token = self.client.post("/api/auth/login", json={
            "username": other, "password": "motdepasse123",
        }).json()["access_token"]
        auth2 = {"Authorization": f"Bearer {token}"}

        r = self.client.get(f"/api/games/{game['id']}/levels", headers=auth2)
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
