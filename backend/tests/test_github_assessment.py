from io import BytesIO
import tarfile

from mission_orchestration.github_assessment import materialize_source


def test_archive_only_materializes_in_scope_regular_files(tmp_path):
    archive_path = tmp_path / 'repository.tar.gz'
    with tarfile.open(archive_path, 'w:gz') as archive:
        for name in ('snapshot/src/app.py', 'snapshot/vendor/dependency.js', 'snapshot/../escaped.py'):
            entry = tarfile.TarInfo(name)
            entry.size = 4
            archive.addfile(entry, BytesIO(b'test'))
        link = tarfile.TarInfo('snapshot/src/link.py')
        link.type = tarfile.SYMTYPE
        link.linkname = '/etc/passwd'
        archive.addfile(link)
    output = tmp_path / 'files'
    output.mkdir()
    names, excluded, gaps = materialize_source(archive_path, output)
    assert names == ['src/app.py']
    assert excluded == 1
    assert gaps == ['unsafe_source_entry']
    assert (output / 'src/app.py').read_bytes() == b'test'
    assert not (tmp_path / 'escaped.py').exists()
    assert not (output / 'src/link.py').is_symlink()
