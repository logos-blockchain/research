"""Execute a runner cell as a subprocess (one process per cell).

One process per cell keeps peak_rss_kb attributable and isolates each
(impl, operation, runtime, params) measurement from the others.
"""
from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

from .protocol import JobSpec, Result
from .registry import Adapter


class RunnerError(RuntimeError):
    pass


# Live runner subprocesses, so a Ctrl+C can kill them promptly instead of leaving
# them running. Worker threads (concurrency/mining) never receive KeyboardInterrupt
# themselves, so the main-thread SIGINT handler (installed in cli.main) reaps them
# via terminate_all_children(); the per-call finally cleans up the common case.
_active: set[subprocess.Popen] = set()
_active_lock = threading.Lock()


def terminate_all_children() -> None:
    """Kill every runner subprocess still running. Safe to call from a signal
    handler (main thread) and idempotent."""
    with _active_lock:
        procs = list(_active)
    for p in procs:
        try:
            p.kill()
        except Exception:  # noqa: BLE001 - best-effort teardown, never raise
            pass


def run(
    adapter: Adapter,
    spec: JobSpec,
    repo_root: Path,
    timeout: float = 900.0,
) -> Result:
    argv = adapter.resolve(repo_root)
    env = dict(os.environ)
    env.update(adapter.env)
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except FileNotFoundError as e:
        raise RunnerError(f"{adapter.name} executable not found: {argv[0]}") from e
    with _active_lock:
        _active.add(proc)
    try:
        stdout, stderr = proc.communicate(input=spec.to_json(), timeout=timeout)
    except subprocess.TimeoutExpired as e:
        proc.kill()
        proc.communicate()  # reap the killed child so it can't linger as a zombie
        raise RunnerError(f"{adapter.name} timed out after {timeout}s") from e
    except BaseException:
        # KeyboardInterrupt (or anything else): never leave the child running.
        proc.kill()
        try:
            proc.communicate(timeout=5)
        except Exception:  # noqa: BLE001
            pass
        raise
    finally:
        with _active_lock:
            _active.discard(proc)

    out = (stdout or "").strip()
    if not out:
        raise RunnerError(
            f"{adapter.name} produced no output (exit {proc.returncode}); "
            f"stderr: {(stderr or '').strip()[:500]}"
        )
    # A runner may print progress lines to stdout before the JSON; take the last line.
    line = out.splitlines()[-1]
    try:
        import json

        result = Result.from_dict(json.loads(line))
    except Exception as e:  # noqa: BLE001
        raise RunnerError(
            f"{adapter.name} emitted invalid result JSON: {e}; "
            f"raw: {line[:500]}"
        ) from e
    return result
