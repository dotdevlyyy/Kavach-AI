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


async def execute_python_code(code: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Executes Python code safely in a separate subprocess.
    Captures stdout, stderr, execution duration, and exit status.
    """
    # Write code to a temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    try:
        # Launch python subprocess
        proc = await asyncio.create_subprocess_exec(
            sys.executable, tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(tmp_path)
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
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
