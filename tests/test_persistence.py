"""Linux-only filesystem regression tests; no Docker or database is started.

Run as root in an isolated Linux test environment:
    python3 -m unittest discover -s tests -v

All fixtures, fake command binaries and ownership changes stay in one fresh
TemporaryDirectory. Numeric account IDs model the image's service accounts;
the test never creates or changes system accounts.
"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PERSIST_SCRIPT = Path(__file__).resolve().parents[1] / "eurooffice_documentserver" / "persist.sh"
ACCOUNTS = {"postgres": (102, 104), "rabbitmq": (103, 105), "redis": (101, 103), "ds": (105, 107)}
SHELL = """
set -Eeuo pipefail
source "$1"
shift
log() { printf '%s\\n' "$*"; }
id() {
  case "$1:$2" in
    -u:postgres) printf 102 ;; -g:postgres) printf 104 ;;
    -u:rabbitmq) printf 103 ;; -g:rabbitmq) printf 105 ;;
    -u:redis) printf 101 ;; -g:redis) printf 103 ;;
    -u:ds) printf 105 ;; -g:ds) printf 107 ;;
    *) return 1 ;;
  esac
}
persist_path "$@"
"""


class PersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.geteuid() != 0:
            raise RuntimeError("These isolated numeric-ownership tests require Linux root.")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="eurooffice-ownership-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "image" / "postgresql"
        self.target = self.root / "data" / "postgresql"

    def existing_state(self, owner=(103, 105)):
        cluster = self.target / "16" / "main"
        cluster.mkdir(parents=True)
        (cluster / "PG_VERSION").write_bytes(b"16\n")
        (cluster / "database.fixture").write_bytes(b"existing database bytes\x00\xff")
        for path in [self.target, *self.target.rglob("*")]:
            os.chown(path, *owner, follow_symlinks=False)
        self.source.parent.mkdir(parents=True)
        self.source.symlink_to(self.target, target_is_directory=True)
        return cluster

    def run_persist(self, owner="postgres", protect=False, check=True, source=None, target=None, env=None):
        result = subprocess.run(
            ["bash", "-c", SHELL, "test-persistence", str(PERSIST_SCRIPT),
             str(source or self.source), str(target or self.target), owner,
             "true" if protect else "false"],
            capture_output=True, text=True, timeout=15, env=env,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def assert_owner(self, path, expected):
        info = path.lstat()
        self.assertEqual((info.st_uid, info.st_gid), expected, str(path))

    def blocked_chown_env(self):
        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        fake_chown = fake_bin / "chown"
        fake_chown.write_text("#!/bin/sh\necho 'chown deliberately denied by test' >&2\nexit 77\n")
        fake_chown.chmod(0o755)
        return {**os.environ, "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"]}

    def test_old_postgres_uid_is_migrated_behind_symlink_without_changing_bytes(self):
        cluster = self.existing_state()
        before = (cluster / "database.fixture").read_bytes()
        # Reproduce the upstream repair: it changes the symlink, but leaves
        # the old numeric owner on the real PostgreSQL cluster unchanged.
        subprocess.run(["chown", "-R", "102:104", str(self.source)], check=True)
        self.assert_owner(self.source, ACCOUNTS["postgres"])
        self.assert_owner(cluster, (103, 105))
        self.run_persist()
        for path in [self.source, self.target, *self.target.rglob("*")]:
            self.assert_owner(path, ACCOUNTS["postgres"])
        self.assertEqual((cluster / "database.fixture").read_bytes(), before)
        self.assertEqual((cluster / "PG_VERSION").read_bytes(), b"16\n")

    def test_correct_top_directory_does_not_hide_old_owners_below_it(self):
        cluster = self.existing_state()
        os.chown(self.target, *ACCOUNTS["postgres"])
        self.run_persist()
        self.assert_owner(cluster / "database.fixture", ACCOUNTS["postgres"])

    def test_fresh_image_directory_is_copied_and_linked(self):
        self.source.mkdir(parents=True)
        data = self.source / "seed.fixture"
        data.write_bytes(b"seed database bytes")
        data.chmod(0o600)
        self.source.chmod(0o700)
        self.run_persist()
        self.assertTrue(self.source.is_symlink())
        self.assertEqual((self.target / "seed.fixture").read_bytes(), b"seed database bytes")
        self.assertEqual(self.target.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.target / "seed.fixture").stat().st_mode & 0o777, 0o600)
        self.assert_owner(self.target / "seed.fixture", ACCOUNTS["postgres"])

    def test_existing_data_is_not_replaced_by_new_image_seed(self):
        cluster = self.existing_state()
        self.source.unlink()
        self.source.mkdir()
        (self.source / "new-image.fixture").write_bytes(b"new image seed")
        self.run_persist()
        self.assertEqual((cluster / "database.fixture").read_bytes(), b"existing database bytes\x00\xff")
        self.assertFalse((self.target / "new-image.fixture").exists())

    def test_empty_persistence_directory_and_missing_image_directory(self):
        self.run_persist()
        self.assertTrue(self.source.is_symlink())
        self.assertEqual(list(self.target.iterdir()), [])
        self.assert_owner(self.target, ACCOUNTS["postgres"])

    def test_each_service_uses_its_own_current_image_account(self):
        services = (("Data", "ds"), ("lib-documentserver", "ds"), ("logs", "ds"),
                    ("postgresql", "postgres"), ("redis", "redis"), ("rabbitmq", "rabbitmq"))
        for name, owner in services:
            with self.subTest(service=name):
                source = self.root / "services" / name
                target = self.root / "persisted-services" / name
                target.mkdir(parents=True)
                (target / "state.fixture").write_bytes(name.encode())
                self.run_persist(owner, name == "Data", source=source, target=target)
                self.assert_owner(source, ACCOUNTS[owner])
                self.assert_owner(target / "state.fixture", ACCOUNTS[owner])

    def test_data_secrets_remain_root_owned_with_contents_and_modes_preserved(self):
        self.existing_state()
        private = self.target / ".private"
        private.mkdir(mode=0o700)
        secret_paths = [private / "jwt.fixture", self.target / "wopi_private.key", self.target / "wopi_public.key"]
        for path in secret_paths:
            path.write_bytes(b"test-only secret fixture")
            path.chmod(0o600)
            os.chown(path, *ACCOUNTS["ds"])
        os.chown(private, *ACCOUNTS["ds"])
        self.run_persist("ds", protect=True)
        for path in [private, *secret_paths]:
            self.assert_owner(path, (0, 0))
        for path in secret_paths:
            self.assertEqual(path.read_bytes(), b"test-only secret fixture")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(private.stat().st_mode & 0o777, 0o700)
        self.assert_owner(self.target / "16" / "main" / "database.fixture", ACCOUNTS["ds"])
        self.run_persist("ds", protect=True, env=self.blocked_chown_env())

    def test_internal_symlink_does_not_change_external_file_or_directory(self):
        self.existing_state()
        outside = self.root / "outside"
        outside.mkdir()
        external = outside / "untouched.fixture"
        external.write_bytes(b"outside the persisted tree")
        os.chown(outside, 12345, 12346)
        os.chown(external, 12345, 12346)
        link = self.target / "external-link"
        link.symlink_to(outside, target_is_directory=True)
        self.run_persist()
        self.assert_owner(link, ACCOUNTS["postgres"])
        self.assert_owner(outside, (12345, 12346))
        self.assert_owner(external, (12345, 12346))
        self.assertEqual(external.read_bytes(), b"outside the persisted tree")

    def test_second_start_does_not_chown_already_correct_data(self):
        self.existing_state()
        self.run_persist()
        self.run_persist(env=self.blocked_chown_env())

    def test_wrong_source_symlink_is_rejected_before_repair(self):
        self.existing_state()
        self.source.unlink()
        outside = self.root / "outside"
        outside.mkdir()
        self.source.symlink_to(outside, target_is_directory=True)
        result = self.run_persist(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected target", result.stdout)
        self.assert_owner(self.target, (103, 105))
        self.assert_owner(outside, (0, 0))

    def test_symlink_as_persistence_target_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(outside, target_is_directory=True)
        result = self.run_persist(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("real directory", result.stdout)
        self.assert_owner(outside, (0, 0))

    def test_file_as_persistence_target_preserves_image_directory_and_file(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"unexpected file")
        self.source.mkdir(parents=True)
        (self.source / "seed.fixture").write_bytes(b"original image seed")
        result = self.run_persist(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("real directory", result.stdout)
        self.assertEqual(self.target.read_bytes(), b"unexpected file")
        self.assertEqual((self.source / "seed.fixture").read_bytes(), b"original image seed")

    def test_missing_account_stops_startup(self):
        self.existing_state()
        result = self.run_persist("missing-account", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot resolve service account", result.stdout)
        self.assert_owner(self.target, (103, 105))

    def test_failed_ownership_change_stops_startup(self):
        self.existing_state()
        result = self.run_persist(check=False, env=self.blocked_chown_env())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("chown deliberately denied", result.stderr)
        self.assert_owner(self.target, (103, 105))


if __name__ == "__main__":
    unittest.main()
