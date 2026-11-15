import asyncio
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from models.remediations import RemediationProposal
from security_engine.executor import ExecutionError
from security_engine.remediation import PatchSafetyError
from security_engine.remediation_workspace import PatchApplicator, RemediationWorkspace


def proposal(patch_text):
    return RemediationProposal(
        summary='Replace unsafe evaluation',
        explanation='Use a parser instead of executing input.',
        affected_files=['app.py'],
        patch=patch_text,
        expected_security_effect='Prevents arbitrary code execution.',
        potential_side_effects=[],
        recommended_tests=['Run parser tests.'],
        confidence=0.95,
    )


PATCH = '''--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-result = eval(value)
+result = parse(value)
'''


def test_workspace_separates_original_and_patched_and_always_cleans(tmp_path):
    roots = []
    for should_raise in (False, True):
        manager = pytest.raises(RuntimeError) if should_raise else nullcontext()
        with manager:
            with RemediationWorkspace('id', parent=tmp_path, max_bytes=1000) as workspace:
                roots.append(workspace.paths.root)
                workspace.paths.original.mkdir()
                (workspace.paths.original / 'app.py').write_text('original', encoding='utf-8')
                workspace.create_patched_copy()
                (workspace.paths.patched / 'app.py').write_text('patched', encoding='utf-8')
                assert (workspace.paths.original / 'app.py').read_text(encoding='utf-8') == 'original'
                if should_raise:
                    raise RuntimeError('test')
        assert not roots[-1].exists()
    assert roots[0] != roots[1]


def test_workspace_limit_counts_both_isolated_trees(tmp_path):
    with RemediationWorkspace('id', parent=tmp_path, max_bytes=7) as workspace:
        workspace.paths.original.mkdir()
        (workspace.paths.original / 'app.py').write_bytes(b'abcd')
        with pytest.raises(ValueError, match='workspace limit'):
            workspace.create_patched_copy()
        assert not workspace.paths.patched.exists()


def test_patch_applies_only_to_patched_tree(tmp_path):
    with RemediationWorkspace('id', parent=tmp_path, max_bytes=10_000) as workspace:
        workspace.paths.original.mkdir()
        (workspace.paths.original / 'app.py').write_text('result = eval(value)\n', encoding='utf-8')
        workspace.create_patched_copy()
        safe = asyncio.run(PatchApplicator().apply(
            proposal(PATCH), workspace, max_bytes=1000, max_files=1, timeout=10,
        ))
        assert safe.files == ('app.py',)
        assert (workspace.paths.original / 'app.py').read_text(encoding='utf-8') == 'result = eval(value)\n'
        assert (workspace.paths.patched / 'app.py').read_text(encoding='utf-8') == 'result = parse(value)\n'
        assert (workspace.paths.artifacts / 'proposal.diff').is_file()


def test_unsafe_patch_is_rejected_before_execution(tmp_path):
    unsafe = PATCH.replace('--- a/app.py', '--- /dev/null')
    with RemediationWorkspace('id', parent=tmp_path, max_bytes=10_000) as workspace:
        workspace.paths.original.mkdir()
        (workspace.paths.original / 'app.py').write_text('result = eval(value)\n', encoding='utf-8')
        workspace.create_patched_copy()
        with patch('security_engine.remediation_workspace.execute', new=AsyncMock()) as execute:
            with pytest.raises(PatchSafetyError):
                asyncio.run(PatchApplicator().apply(
                    proposal(unsafe), workspace, max_bytes=1000, max_files=1, timeout=10,
                ))
        execute.assert_not_awaited()


def test_patch_check_failure_is_controlled(tmp_path):
    failed = SimpleNamespace(exit_code=1, stdout=b'', stderr=b'failure')
    with RemediationWorkspace('id', parent=tmp_path, max_bytes=10_000) as workspace:
        workspace.paths.original.mkdir()
        (workspace.paths.original / 'app.py').write_text('result = eval(value)\n', encoding='utf-8')
        workspace.create_patched_copy()
        with patch('security_engine.remediation_workspace.shutil.which', return_value='git'), \
             patch('security_engine.remediation_workspace.execute', new=AsyncMock(return_value=failed)):
            with pytest.raises(ExecutionError, match='safely'):
                asyncio.run(PatchApplicator().apply(
                    proposal(PATCH), workspace, max_bytes=1000, max_files=1, timeout=10,
                ))
