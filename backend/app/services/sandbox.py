import os
import sys
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import docker
from app.config import settings
from app.services.telemetry import telemetry_service

class SandboxExecutionResult:
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_ms: int,
        timed_out: bool = False,
        failure_type: str = "none",
        output_files: Optional[list] = None
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_ms = duration_ms
        self.timed_out = timed_out
        self.failure_type = failure_type
        self.output_files = output_files or []

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

class SandboxService:
    def __init__(self):
        self.use_docker = settings.USE_DOCKER_SANDBOX
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS
        self.memory_limit = settings.SANDBOX_MEMORY_LIMIT
        self.cpu_limit = settings.SANDBOX_CPU_LIMIT
        self.image = settings.SANDBOX_IMAGE

    def _execute_subprocess(
        self, script_path: Path, dataset_path: Path, output_dir: Path
    ) -> SandboxExecutionResult:
        start_time = time.time()
        timed_out = False

        # Scrub environment variables - never expose API keys or secrets
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PYTHONPATH": "",
            "MPLCONFIGDIR": str(output_dir),
        }

        # Prepare workspace where script expects 'data/input.<ext>'
        work_dir = output_dir.parent / "workspace"
        work_dir.mkdir(parents=True, exist_ok=True)
        data_dir = work_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Link or copy dataset to expected input path
        ext = dataset_path.suffix
        workspace_dataset = data_dir / f"input{ext}"
        if not workspace_dataset.exists():
            shutil.copyfile(dataset_path, workspace_dataset)

        workspace_outputs = work_dir / "outputs"
        workspace_outputs.mkdir(parents=True, exist_ok=True)

        # Inject sandbox security guard preventing socket connections
        preamble = (
            "import socket\n"
            "def _blocked_connect(*args, **kwargs):\n"
            "    raise PermissionError('Network access is disabled inside the analysis sandbox.')\n"
            "socket.socket.connect = _blocked_connect\n"
            "socket.create_connection = _blocked_connect\n"
        )
        safe_script_path = work_dir / "safe_exec.py"
        with open(script_path, "r", encoding="utf-8") as sf:
            user_script = sf.read()
        with open(safe_script_path, "w", encoding="utf-8") as df:
            df.write(preamble + "\n" + user_script)

        python_exe = sys.executable

        try:
            process = subprocess.run(
                [python_exe, str(safe_script_path.resolve())],
                cwd=str(work_dir.resolve()),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            stdout = process.stdout
            stderr = process.stderr
            exit_code = process.returncode
        except subprocess.TimeoutExpired as te:
            timed_out = True
            stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
            stderr = f"Execution timed out after {self.timeout} seconds."
            exit_code = 124
        except Exception as e:
            stdout = ""
            stderr = f"Sandbox execution error: {str(e)}"
            exit_code = 1

        duration_ms = int((time.time() - start_time) * 1000)
        failure_type = telemetry_service.classify_failure(exit_code, stdout, stderr, timed_out=timed_out)

        # Collect output files with quota caps (max 20 files, max 50MB per file)
        output_files = []
        if workspace_outputs.exists():
            candidates = list(workspace_outputs.glob("*"))[:20]
            for f in candidates:
                if f.is_file() and f.stat().st_size <= 50 * 1024 * 1024:
                    target = output_dir / f.name
                    shutil.copyfile(f, target)
                    output_files.append(str(target.resolve()))

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            failure_type=failure_type,
            output_files=output_files
        )

    def _execute_docker(
        self, script_path: Path, dataset_path: Path, output_dir: Path
    ) -> SandboxExecutionResult:
        start_time = time.time()
        client = docker.from_env()

        ext = dataset_path.suffix
        volumes = {
            str(script_path.resolve()): {"bind": "/workspace/code.py", "mode": "ro"},
            str(dataset_path.resolve()): {"bind": f"/workspace/data/input{ext}", "mode": "ro"},
            str(output_dir.resolve()): {"bind": "/workspace/outputs", "mode": "rw"}
        }

        timed_out = False
        try:
            container = client.containers.run(
                self.image,
                network_mode="none",
                mem_limit=self.memory_limit,
                nano_cpus=int(self.cpu_limit * 1e9),
                volumes=volumes,
                detach=True,
                remove=False
            )
            
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result.get("StatusCode", 1)
                logs = container.logs(stdout=True, stderr=True)
                stdout = logs.decode("utf-8", errors="replace")
                stderr = ""
            except Exception:
                # Timed out
                timed_out = True
                container.kill()
                exit_code = 124
                stdout = ""
                stderr = f"Container execution timed out after {self.timeout} seconds."
            finally:
                container.remove(force=True)

        except Exception as e:
            # Fall back to isolated subprocess if docker image is not built or daemon fails
            return self._execute_subprocess(script_path, dataset_path, output_dir)

        duration_ms = int((time.time() - start_time) * 1000)
        failure_type = telemetry_service.classify_failure(exit_code, stdout, stderr, timed_out=timed_out)

        output_files = [str(f.resolve()) for f in output_dir.glob("*")]

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            failure_type=failure_type,
            output_files=output_files
        )

    def execute_code(
        self, code: str, dataset_path: str, run_id: str, attempt: int
    ) -> SandboxExecutionResult:
        run_temp_dir = Path(settings.OUTPUT_DIR) / f"run_{run_id}" / f"attempt_{attempt}"
        run_temp_dir.mkdir(parents=True, exist_ok=True)
        output_dir = run_temp_dir / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        script_path = run_temp_dir / "code.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        dataset = Path(dataset_path)

        if self.use_docker:
            return self._execute_docker(script_path, dataset, output_dir)
        else:
            return self._execute_subprocess(script_path, dataset, output_dir)

sandbox_service = SandboxService()
