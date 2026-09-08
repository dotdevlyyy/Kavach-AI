"""
Kavach AI — Sandboxed Code Runner
Executes Python code in a sandboxed subprocess with execution timeouts,
memory limits, and stdout/stderr capture.
"""

import sys
import os
import asyncio
import tempfile
from typing import Dict, Any
from loguru import logger

# ponytail: 512 MB cap matches docs/03 + docs/14. Enforced POSIX-only via
# resource.setrlimit in preexec_fn — no-op on Windows.
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024


def _limit_memory():
    """Posix preexec_fn: cap address space before exec."""
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    except (ImportError, ValueError, OSError):
        pass


async def execute_python_code(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Executes Python code safely in a separate subprocess.
    Captures stdout, stderr, execution duration, and exit status.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, "script.py")
        with open(tmp_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(code)

        try:
            # Launch python subprocess with empty env and dropped parent env.
            # The tmp_dir is the cwd so the script can't reach into backend/data.
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmp_dir,
                env={},
                preexec_fn=_limit_memory if os.name == "posix" else None,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "output": stdout if stdout else stderr
                }
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds.",
                    "output": f"Execution timed out after {timeout} seconds."
                }

        except Exception as e:
            logger.error(f"Error executing Python sandbox code: {e}")
            return {
                "success": False,
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "output": str(e)
            }
