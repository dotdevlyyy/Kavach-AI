"""Run generated Python only inside a locked-down, pre-provisioned container."""

import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
SANDBOX_IMAGE = "python:3.13-slim"


def _result(success: bool, exit_code: int, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    return {
        "success": success,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "output": stdout if stdout else stderr,
    }


async def _image_is_local(docker: str) -> bool:
    def _run():
        return subprocess.run(
            [docker, "image", "inspect", SANDBOX_IMAGE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
    return await asyncio.to_thread(_run)


async def _remove_container(docker: str, name: str) -> None:
    def _run():
        subprocess.run(
            [docker, "rm", "-f", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    await asyncio.to_thread(_run)


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
        stdout_path = root / "stdout.txt"
        stderr_path = root / "stderr.txt"
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

        try:
            def _run_docker():
                with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
                    return subprocess.run(
                        command,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        env=os.environ.copy(),
                        timeout=timeout,
                    ).returncode

            try:
                exit_code = await asyncio.to_thread(_run_docker)
            except subprocess.TimeoutExpired:
                await _remove_container(docker, container_name)
                return _result(
                    False,
                    -1,
                    stderr=f"Execution timed out after {timeout} seconds.",
                )

            if (
                stdout_path.stat().st_size > MAX_OUTPUT_BYTES
                or stderr_path.stat().st_size > MAX_OUTPUT_BYTES
            ):
                return _result(False, exit_code, stderr="Execution output exceeded 1 MB.")

            stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
            stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
            return _result(exit_code == 0, exit_code, stdout, stderr)
        except Exception as exc:
            logger.exception(f"Secure code sandbox failed: {exc}")
            return _result(False, 1, stderr="Secure code sandbox failed.")
