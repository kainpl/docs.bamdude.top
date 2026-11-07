"""Linux-only orchestration tests; no Docker daemon, downloads or printers used.

The CLI fakes exercise the real Bash helper. They do not test model inference.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "docs/assets/downloads/obico-ml.sh"
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as stream:
    stream.write(json.dumps([name, args]) + '\n')
if name == 'git':
    if args[0] == 'clone':
        pathlib.Path(args[-1], 'ml_api').mkdir(parents=True)
    elif 'get-url' in args:
        print('https://github.com/TheSpaghettiDetective/obico-server.git')
    elif '--show-current' in args:
        print('release')
    elif 'status' in args:
        print(os.environ.get('DIRTY', ''), end='')
    elif 'rev-parse' in args:
        print('abcdef0')
elif name == 'docker':
    if '--services' in args:
        assert not any(key in os.environ for key in (
            'ML_BIND', 'ML_PORT', 'ML_TOKEN', 'ML_PROJECT',
            'COMPOSE_FILE', 'COMPOSE_PROFILES', 'COMPOSE_PROJECT_NAME', 'COMPOSE_ENV_FILES'))
        print(os.environ.get('SERVICES', 'ml_api'))
    if 'build' in args and os.environ.get('BUILD_FAIL'):
        sys.exit(17)
    if 'up' in args and os.environ.get('UP_FAIL'):
        sys.exit(18)
elif name == 'curl':
    if args[-1].endswith('/hc/'):
        print(os.environ.get('HEALTH', 'ok'))
    elif '--config' in args:
        header = sys.stdin.read()
        assert 'Authorization: Bearer ' in header
        print(os.environ.get('AUTH_CODE', '422'))
    else:
        print(os.environ.get('NOAUTH_CODE', '401'))
'''


@unittest.skipUnless(os.name == "posix", "Requires Linux Bash and flock")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="obico-ml-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "install with spaces"
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name in ("git", "docker", "curl"):
            path = self.bin / name
            path.write_text(FAKE)
            path.chmod(0o755)
        self.calls_path = self.base / "calls.jsonl"
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", CALLS=str(self.calls_path))

    def invoke(self, action, *extra, ok=True, **env):
        result = subprocess.run(
            ["bash", str(SCRIPT), action, str(self.root), *extra],
            env=dict(self.env, **env), capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def calls(self):
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()]

    def clear(self):
        self.calls_path.write_text("")

    def install(self):
        return self.invoke("install", "127.0.0.1", "3333")

    def test_install_only_builds_and_starts_ml_without_exposing_secret(self):
        result = self.install()
        calls = self.calls()
        build = next(args for name, args in calls if name == "docker" and "build" in args)
        up = next(args for name, args in calls if name == "docker" and "up" in args)
        self.assertEqual(build[-3:], ["build", "--pull", "ml_api"])
        self.assertEqual(up[-8:], ["up", "-d", "--no-deps", "--no-build", "--wait", "--wait-timeout", "300", "ml_api"])
        config = (self.root / ".env").read_text()
        token = next(line.split("=", 1)[1] for line in config.splitlines() if line.startswith("ML_TOKEN="))
        self.assertNotIn(token, result.stdout + result.stderr + self.calls_path.read_text())
        self.assertEqual((self.root / ".env").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.invoke("token").stdout.strip(), token)
        self.assertEqual((self.root / "obico-ml.sh").read_bytes(), SCRIPT.read_bytes())

    def test_update_preserves_token_and_build_precedes_replace(self):
        self.install()
        original = (self.root / ".env").read_bytes()
        self.clear()
        self.invoke("update")
        calls = self.calls()
        self.assertEqual((self.root / ".env").read_bytes(), original)
        self.assertLess(next(i for i, (_, a) in enumerate(calls) if "build" in a),
                        next(i for i, (_, a) in enumerate(calls) if "up" in a))
        self.assertTrue(any("--ff-only" in a for _, a in calls))
        self.assertFalse(any(x in a for _, a in calls for x in ("down", "prune", "--remove-orphans")))

    def test_failed_build_never_replaces_container(self):
        self.install()
        self.clear()
        self.invoke("update", ok=False, BUILD_FAIL="1")
        self.assertFalse(any("up" in args for _, args in self.calls()))

    def test_failed_replace_reports_failure_without_rollback(self):
        self.install()
        self.clear()
        self.invoke("update", ok=False, UP_FAIL="1")
        self.assertEqual(sum("up" in args for _, args in self.calls()), 1)
        self.assertFalse(any(name == "curl" for name, _ in self.calls()))

    def test_check_does_not_fetch_build_restart_or_probe(self):
        self.install()
        self.clear()
        self.invoke("check")
        self.assertFalse(any(name == "curl" or any(x in args for x in ("fetch", "build", "up", "merge"))
                             for name, args in self.calls()))

    def test_refuses_existing_directory_without_changing_files(self):
        self.install()
        original = (self.root / ".env").read_bytes()
        self.clear()
        self.invoke("install", ok=False)
        self.assertEqual((self.root / ".env").read_bytes(), original)
        self.assertFalse(any("up" in args or "clone" in args for _, args in self.calls()))

    def test_scope_guard_rejects_extra_services_before_fetch(self):
        self.install()
        self.clear()
        self.invoke("update", ok=False, SERVICES="ml_api\nredis")
        self.assertFalse(any("fetch" in args or "up" in args for _, args in self.calls()))

    def test_dirty_checkout_is_preserved(self):
        self.install()
        self.clear()
        self.invoke("update", ok=False, DIRTY=" M ml_api/server.py")
        self.assertFalse(any("fetch" in args or "up" in args for _, args in self.calls()))

    def test_compose_environment_cannot_replace_saved_settings(self):
        self.install()
        self.invoke("check", ML_BIND="0.0.0.0", ML_PORT="1", ML_TOKEN="other", ML_PROJECT="other",
                    COMPOSE_FILE="other.yml", COMPOSE_PROFILES="full-stack",
                    COMPOSE_PROJECT_NAME="other", COMPOSE_ENV_FILES="other.env")

    def test_false_health_and_auth_are_failures(self):
        self.install()
        for env in ({"HEALTH": "error"}, {"NOAUTH_CODE": "422"}, {"AUTH_CODE": "401"}):
            with self.subTest(env=env):
                self.invoke("update", ok=False, **env)

    def test_configuration_is_never_executed_as_shell(self):
        self.install()
        marker = self.base / "must-not-exist"
        with (self.root / ".env").open("a") as stream:
            stream.write(f'\nUNUSED=$(touch "{marker}")\n')
        self.invoke("check")
        self.assertFalse(marker.exists())

    def test_directory_lock_rejects_second_process(self):
        import fcntl
        self.install()
        with (self.root / ".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.clear()
            self.invoke("update", ok=False)
            self.assertEqual(self.calls(), [])

    def test_rejects_invalid_bind_and_port_before_creating_installation(self):
        for bind, port in (("0.0.0.0", "3333"), ("999.1.2.3", "3333"), ("127.0.0.1", "65536")):
            with self.subTest(bind=bind, port=port):
                self.invoke("install", bind, port, ok=False)
                self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
