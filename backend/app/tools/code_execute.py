"""Run generated Python only inside a locked-down, pre-provisioned container."""

import asyncio
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
SANDBOX_IMAGE = "python:3.13-slim"
DOCKER_CONTROL_TIMEOUT_SECONDS = 5


def _result(success: bool, exit_code: int, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    return {
        "success": success,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "output": stdout if stdout else stderr,
    }


async def _image_is_local(docker: str) -> bool:
    process = await asyncio.create_subprocess_exec(
        docker,
        "image",
        "inspect",
        SANDBOX_IMAGE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        return (
            await asyncio.wait_for(process.wait(), timeout=DOCKER_CONTROL_TIMEOUT_SECONDS) == 0
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return False


async def _remove_container(docker: str, name: str) -> None:
    process = await asyncio.create_subprocess_exec(
        docker,
        "rm",
        "-f",
        name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        await asyncio.wait_for(process.wait(), timeout=DOCKER_CONTROL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        logger.warning(f"Timed out removing sandbox container {name}")


class _OutputLimitExceeded(Exception):
    pass


async def _read_limited(stream: asyncio.StreamReader | None) -> bytes:
    output = bytearray()
    if stream is None:
        return bytes(output)
    while chunk := await stream.read(64 * 1024):
        output.extend(chunk)
        if len(output) > MAX_OUTPUT_BYTES:
            raise _OutputLimitExceeded
    return bytes(output)


async def execute_python_code(code: str, timeout: int = 30) -> dict[str, Any]:
    """Execute Python with no network or host access beyond a read-only script mount."""
    docker = shutil.which("docker")
    if not docker:
        return _result(False, 1, stderr="Secure code sandbox unavailable: Docker is not installed.")
    if not await _image_is_local(docker):
        return _result(
            False,
            1,
            stderr=f"Secure code sandbox unavailable: local image {SANDBOX_IMAGE} is missing.",
        )

    timeout = max(1, min(int(timeout), 30))
    container_name = f"kavach-sandbox-{uuid.uuid4().hex}"

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        script = root / "script.py"
        script.write_text(code, encoding="utf-8")

        mount = f"type=bind,source={root},target=/workspace,readonly"
        command = [
            docker,
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--memory",
            str(MEMORY_LIMIT_BYTES),
            "--cpus",
            "1",
            "--pids-limit",
            "64",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            "65534:65534",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--mount",
            mount,
            SANDBOX_IMAGE,
            "python",
            "-I",
            "-B",
            "/workspace/script.py",
        ]

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_task = asyncio.create_task(_read_limited(process.stdout))
            stderr_task = asyncio.create_task(_read_limited(process.stderr))
            try:
                stdout_bytes, stderr_bytes, exit_code = await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, process.wait()), timeout=timeout
                )
            except _OutputLimitExceeded:
                process.kill()
                await process.wait()
                return _result(False, -1, stderr="Execution output exceeded 1 MB.")
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return _result(
                    False,
                    -1,
                    stderr=f"Execution timed out after {timeout} seconds.",
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return _result(exit_code == 0, exit_code, stdout, stderr)
        except Exception as exc:
            logger.exception(f"Secure code sandbox failed: {exc}")
            return _result(False, 1, stderr="Secure code sandbox failed.")
        finally:
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            await asyncio.shield(_remove_container(docker, container_name))
