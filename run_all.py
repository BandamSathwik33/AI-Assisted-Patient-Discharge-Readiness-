"""Cross-Platform Multi-Service Runner for AI-Assisted Patient Discharge Planner.

Launches the 4 backend microservices concurrently with colored log prefixing and
graceful Ctrl+C shutdown across Windows, macOS, and Linux.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# ANSI Color Codes for terminal log distinction
COLORS = {
    "AUTH": "\033[95m",     # Magenta
    "BACKEND": "\033[94m",  # Blue
    "AI": "\033[96m",       # Cyan
    "NLP": "\033[93m",      # Yellow
    "SYSTEM": "\033[92m",   # Green
    "ERROR": "\033[91m",    # Red
    "RESET": "\033[0m",     # Reset
}

# Enable ANSI color support on Windows command prompt if needed
if os.name == "nt":
    try:
        import colorama
        colorama.just_fix_windows_console()
    except ImportError:
        os.system("")  # Enables ANSI sequences in modern Windows console

WORKSPACE_ROOT = Path(__file__).resolve().parent

SERVICES = [
    {
        "name": "AUTH",
        "dir": WORKSPACE_ROOT / "discharge-auth-service",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"],
        "port": 8003,
    },
    {
        "name": "BACKEND",
        "dir": WORKSPACE_ROOT / "discharge-backend-core",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        "port": 8000,
    },
    {
        "name": "AI",
        "dir": WORKSPACE_ROOT / "discharge-ai-orchestrator",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
        "port": 8001,
    },
    {
        "name": "NLP",
        "dir": WORKSPACE_ROOT / "discharge-nlp-data",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"],
        "port": 8002,
    },
]

processes = []
stop_event = threading.Event()


def log_streamer(service_name: str, pipe, color_code: str):
    """Continuously reads from a subprocess pipe and prints with color-prefixed tags."""
    try:
        for line in iter(pipe.readline, b""):
            if stop_event.is_set():
                break
            text = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if text:
                print(f"{color_code}[{service_name:^7}]{COLORS['RESET']} {text}", flush=True)
    except Exception:
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def start_service(service_info):
    """Starts an individual microservice process."""
    name = service_info["name"]
    cwd = service_info["dir"]
    cmd = service_info["cmd"]
    port = service_info["port"]
    color = COLORS.get(name, COLORS["SYSTEM"])

    if not cwd.exists():
        print(
            f"{COLORS['ERROR']}[{name:^7}]{COLORS['RESET']} Directory {cwd} does not exist. (Skipping)",
            flush=True,
        )
        return None

    # Check if entry file exists in directory
    main_py = cwd / "main.py"
    if not main_py.exists():
        print(
            f"{COLORS['ERROR']}[{name:^7}]{COLORS['RESET']} No main.py found in {cwd}. (Skipping)",
            flush=True,
        )
        return None

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PORT"] = str(port)

    print(
        f"{COLORS['SYSTEM']}[SYSTEM]{COLORS['RESET']} Launching {color}{name}{COLORS['RESET']} service on port {port}...",
        flush=True,
    )

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            bufsize=1,
        )

        t = threading.Thread(
            target=log_streamer,
            args=(name, proc.stdout, color),
            daemon=True,
        )
        t.start()
        return proc
    except Exception as e:
        print(
            f"{COLORS['ERROR']}[SYSTEM]{COLORS['RESET']} Failed to start {name}: {e}",
            flush=True,
        )
        return None


def terminate_all_processes(signum=None, frame=None):
    """Gracefully terminates all active subprocesses."""
    print(f"\n{COLORS['SYSTEM']}[SYSTEM]{COLORS['RESET']} Shutting down all services...", flush=True)
    stop_event.set()

    for p in processes:
        if p and p.poll() is None:
            try:
                if os.name == "nt":
                    # On Windows, terminate gently then kill if needed
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    p.terminate()
            except Exception:
                pass

    time.sleep(1.0)
    for p in processes:
        if p and p.poll() is None:
            try:
                p.kill()
            except Exception:
                pass

    print(f"{COLORS['SYSTEM']}[SYSTEM]{COLORS['RESET']} All backend microservices stopped.", flush=True)
    sys.exit(0)


def main():
    print("=" * 70)
    print(f"{COLORS['SYSTEM']} AI-ASSISTED PATIENT DISCHARGE PLANNER - MULTI-SERVICE RUNNER{COLORS['RESET']}")
    print("=" * 70)
    print("Microservices:")
    print("  • discharge-auth-service      -> http://localhost:8003")
    print("  • discharge-backend-core      -> http://localhost:8000")
    print("  • discharge-ai-orchestrator   -> http://localhost:8001")
    print("  • discharge-nlp-data          -> http://localhost:8002")
    print("Frontend App (Vite Dev):")
    print("  • discharge-frontend          -> http://localhost:5173 (run 'npm run dev')")
    print("=" * 70)
    print("Press Ctrl+C to terminate all services cleanly.\n")

    signal.signal(signal.SIGINT, terminate_all_processes)
    signal.signal(signal.SIGTERM, terminate_all_processes)

    for service_info in SERVICES:
        proc = start_service(service_info)
        if proc:
            processes.append(proc)

    if not processes:
        print(f"{COLORS['ERROR']}[SYSTEM] No services were started.{COLORS['RESET']}")
        sys.exit(1)

    try:
        while True:
            time.sleep(0.5)
            # Check if all processes terminated unexpectedly
            active = [p for p in processes if p.poll() is None]
            if not active:
                print(f"{COLORS['SYSTEM']}[SYSTEM] All child processes have exited.{COLORS['RESET']}")
                break
    except KeyboardInterrupt:
        terminate_all_processes()


if __name__ == "__main__":
    main()
