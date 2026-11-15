"""Regressões de isolamento de caminhos sensíveis no sandbox."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pluto import tools


class SensitivePathSandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workdir = self.root / "workspace"
        self.workdir.mkdir()
        self.data_dir = self.workdir / "pluto-data"
        self.secrets = self.data_dir / "secrets"
        self.secrets.mkdir(parents=True)
        self.secret_file = self.secrets / "token.key"
        self.secret_file.write_text("fake-test-token", encoding="utf-8")
        self.public_file = self.workdir / "notes.txt"
        self.public_file.write_text("public", encoding="utf-8")
        self.cfg = SimpleNamespace(sandbox=True, workdir=self.workdir,
                                   data_dir=self.data_dir, skills_dirs=[],
                                   sandbox_home_read=True)

    def test_workspace_secret_is_denied(self):
        with self.assertRaises(tools.ToolError):
            tools.resolve_path(str(self.secret_file), self.cfg)

    def test_secret_is_denied_when_skills_dir_is_allowlisted(self):
        self.cfg.skills_dirs = [self.secrets]
        with self.assertRaises(tools.ToolError):
            tools.resolve_path(str(self.secret_file), self.cfg)

    def test_secret_is_denied_in_active_scope(self):
        with patch.object(tools, "scope_dir", return_value=self.secrets):
            with self.assertRaises(tools.ToolError):
                tools.resolve_path("token.key", self.cfg)

    def test_symlink_into_secrets_is_denied(self):
        link = self.workdir / "alias.key"
        try:
            link.symlink_to(self.secret_file)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable on this platform")
        with self.assertRaises(tools.ToolError):
            tools.resolve_path(str(link), self.cfg)

    def test_workspace_alias_is_normalized_before_allowlist(self):
        with patch.object(tools, "scope_dir", return_value=None):
            alias = self.root / "workspace-alias"
            try:
                alias.symlink_to(self.workdir, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink unavailable on this platform")
            self.cfg.workdir = alias
            self.assertEqual(tools.resolve_path("notes.txt", self.cfg),
                             self.public_file.resolve())
            with self.assertRaises(tools.ToolError):
                tools.resolve_path("pluto-data/secrets/token.key", self.cfg)

    def test_normal_workspace_read_still_allowed(self):
        self.assertEqual(tools.resolve_path(str(self.public_file), self.cfg),
                         self.public_file.resolve())


if __name__ == "__main__":
    unittest.main()
