"""Host-side sandbox runner: execute agent code in an ephemeral Docker container.

Security posture (see docs/Agent改进方案.md §5):
  --network none        no outbound anything
  --memory/--cpus/pids  resource caps
  --read-only rootfs    + tmpfs for scratch
  non-root user         (baked into the image)
  --rm                  container discarded after each run
  timeout               host-side kill if it overruns

Nothing the agent writes touches the host except the JSON it drops in out/.
"""
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

IMAGE = "quant-sandbox:latest"
HARNESS_DIR = Path(__file__).resolve().parent  # holds entry.py + engine_run.py
DEFAULT_TIMEOUT = 30  # seconds


class SandboxError(Exception):
    pass


def run_code(code: str, data_dir: Path, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run agent `code` (defines build_signals + CODE) against datasets in
    `data_dir`. Returns the parsed result dict from the sandbox.
    """
    work = Path(tempfile.mkdtemp(prefix="qsbx_"))
    try:
        (work / "strategy.py").write_text(code, encoding="utf-8")
        (work / "out").mkdir()

        cname = f"qsbx_{uuid.uuid4().hex[:12]}"
        cmd = _docker_cmd(cname, work, data_dir)
        proc = _run(cmd, timeout, cname)

        result_fp = work / "out" / "result.json"
        if not result_fp.exists():
            raise SandboxError(
                f"no result produced (exit={proc.returncode}); "
                f"stderr: {proc.stderr[-800:]}"
            )
        return json.loads(result_fp.read_text(encoding="utf-8"))
    finally:
        _rmtree(work)


def _docker_cmd(cname: str, work: Path, data_dir: Path) -> list[str]:
    """Build the `docker run` argv with the full security posture."""
    def mnt(host: Path, dst: str, ro=True):
        h = str(host).replace("\\", "/")
        return ["-v", f"{h}:{dst}:ro" if ro else f"{h}:{dst}"]

    return [
        "docker", "run", "--rm", "--name", cname,
        "--network", "none",
        "--memory", "512m", "--cpus", "1.0", "--pids-limit", "128",
        "--read-only", "--tmpfs", "/tmp:size=64m",
        "--security-opt", "no-new-privileges",
        *mnt(HARNESS_DIR, "/harness", ro=True),
        *mnt(data_dir, "/data", ro=True),
        *mnt(work, "/work", ro=False),  # strategy.py + out/ (writable)
        IMAGE,
        "python", "/harness/entry.py",
    ]


def _run(cmd: list[str], timeout: int, cname: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        # Best-effort kill of the overrunning container, then surface the timeout.
        subprocess.run(["docker", "kill", cname], capture_output=True, text=True)
        raise SandboxError(f"execution exceeded {timeout}s and was killed")


def _rmtree(p: Path):
    import shutil
    shutil.rmtree(p, ignore_errors=True)


def ensure_image() -> bool:
    """True if the sandbox image exists locally."""
    r = subprocess.run(
        ["docker", "image", "inspect", IMAGE], capture_output=True, text=True
    )
    return r.returncode == 0

