"""Bounded argument-array process execution with no shell."""
import asyncio
from dataclasses import dataclass
from pathlib import Path
import os


class ExecutionError(RuntimeError):
    pass


class DependencyUnavailable(ExecutionError):
    pass


class ExecutionTimeout(ExecutionError):
    pass


class OutputLimitExceeded(ExecutionError):
    pass


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int
    stdout: bytes
    stderr: bytes


async def execute(arguments, *, cwd, timeout, max_output_bytes, environment, artifact_prefix):
    """Arguments/executable must be chosen by adapters, never passed from an HTTP body."""
    stdout_path = Path(artifact_prefix + '.stdout')
    stderr_path = Path(artifact_prefix + '.stderr')
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
        process = await asyncio.create_subprocess_exec(*arguments, cwd=cwd, stdout=stdout, stderr=stderr,
                                                       env=environment, shell=False)
        loop, started = asyncio.get_running_loop(), asyncio.get_running_loop().time()
        try:
            while process.returncode is None:
                if loop.time() - started >= timeout:
                    raise ExecutionTimeout('External operation timed out')
                if stdout_path.stat().st_size + stderr_path.stat().st_size > max_output_bytes:
                    raise OutputLimitExceeded('External operation exceeded its output limit')
                try:
                    await asyncio.wait_for(process.wait(), timeout=min(.1, timeout))
                except TimeoutError:
                    pass
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
        if stdout_path.stat().st_size + stderr_path.stat().st_size > max_output_bytes:
            raise OutputLimitExceeded('External operation exceeded its output limit')
    return ProcessResult(process.returncode, stdout_path.read_bytes(), stderr_path.read_bytes())


def controlled_environment():
    permitted = ['PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR', 'LANG', 'LC_ALL', 'HOME', 'USERPROFILE']
    return {name: os.environ[name] for name in permitted if name in os.environ} | {
        'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_NOSYSTEM': '1', 'SEMGREP_SEND_METRICS': 'off',
        'PYTHONIOENCODING': 'utf-8', 'NO_COLOR': '1'}
