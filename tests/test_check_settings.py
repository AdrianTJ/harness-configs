import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_settings", Path(__file__).resolve().parent.parent / "scripts" / "check-settings.py"
)
check_settings = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_settings)


class CheckSettingsTests(unittest.TestCase):
    def make_root(self, settings):
        root = Path(tempfile.mkdtemp())
        (root / "claude-code" / "hooks").mkdir(parents=True)
        (root / "claude-code" / "hooks" / "guard.sh").write_text("#!/bin/sh\n")
        (root / "claude-code" / "settings.json").write_text(json.dumps(settings))
        return root

    def hook(self, command):
        return {"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": command}]}]}}

    def test_tracked_hook_passes(self):
        root = self.make_root(self.hook('bash "$HOME/.claude/hooks/guard.sh"'))
        self.assertEqual(check_settings.main(root), 0)

    def test_untracked_hook_script_fails(self):
        root = self.make_root(self.hook('bash "$HOME/.claude/hooks/other-agent-state.sh"'))
        self.assertEqual(check_settings.main(root), 1)

    def test_status_line_fails(self):
        root = self.make_root({"statusLine": {"type": "command", "command": "x"}})
        self.assertEqual(check_settings.main(root), 1)

    def test_oversized_settings_fail(self):
        root = self.make_root({"blob": "x" * 9000})
        self.assertEqual(check_settings.main(root), 1)

    def test_named_app_fails(self):
        root = self.make_root(self.hook('bash "$HOME/.orca/agent-hooks/claude-hook.sh"'))
        self.assertEqual(check_settings.main(root), 1)


if __name__ == "__main__":
    unittest.main()
