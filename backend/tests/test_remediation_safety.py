from pathlib import Path
import pytest

from models.remediations import RemediationProposal
from security_engine.remediation import PatchSafetyError, validate_patch


def proposal(patch=None, files=None):
    return RemediationProposal(
        summary='Replace dynamic evaluation', explanation='Parse the value without executing it.',
        affected_files=files or ['app.py'],
        patch=patch or '--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-eval(value)\n+parse(value)\n',
        expected_security_effect='Removes dynamic code execution.',
        potential_side_effects=['Input syntax may be more restricted.'],
        recommended_tests=['Exercise accepted and rejected input values.'], confidence=0.9)


def repository(tmp_path):
    (tmp_path / 'app.py').write_text('eval(value)\n', encoding='utf-8')
    return tmp_path


def test_valid_existing_relative_text_patch(tmp_path):
    result = validate_patch(proposal(), repository(tmp_path), max_bytes=4096, max_files=2)
    assert result.files == ('app.py',) and result.size_bytes == len(result.text.encode())


@pytest.mark.parametrize('patch', [
    '--- /app.py\n+++ /app.py\n@@ -1 +1 @@\n-x\n+y\n',
    '--- a/../outside.py\n+++ b/../outside.py\n@@ -1 +1 @@\n-x\n+y\n',
    '--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+x\n',
])
def test_absolute_traversal_and_new_file_paths_are_rejected(tmp_path, patch):
    with pytest.raises(PatchSafetyError):
        validate_patch(proposal(patch), repository(tmp_path), max_bytes=4096, max_files=2)


def test_symlink_targets_are_rejected_even_when_they_resolve_inside(tmp_path, monkeypatch):
    root = repository(tmp_path)
    (root / 'link.py').write_text('eval(value)\n', encoding='utf-8')
    patch = '--- a/link.py\n+++ b/link.py\n@@ -1 +1 @@\n-eval(value)\n+parse(value)\n'
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda self: self.name == 'link.py' or original(self))
    with pytest.raises(PatchSafetyError, match='symbolic'):
        validate_patch(proposal(patch, ['link.py']), root, max_bytes=4096, max_files=2)


def test_size_file_count_malformed_and_declared_file_mismatch_are_rejected(tmp_path):
    root = repository(tmp_path)
    (root / 'other.py').write_text('x\n', encoding='utf-8')
    with pytest.raises(PatchSafetyError, match='size'):
        validate_patch(proposal(), root, max_bytes=10, max_files=2)
    multi = ('--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x\n+y\n'
             '--- a/other.py\n+++ b/other.py\n@@ -1 +1 @@\n-x\n+y\n')
    with pytest.raises(PatchSafetyError, match='file limit'):
        validate_patch(proposal(multi, ['app.py', 'other.py']), root, max_bytes=4096, max_files=1)
    with pytest.raises(PatchSafetyError, match='malformed'):
        validate_patch(proposal('not a diff'), root, max_bytes=4096, max_files=2)
    with pytest.raises(PatchSafetyError, match='do not match'):
        validate_patch(proposal(files=['other.py']), root, max_bytes=4096, max_files=2)
