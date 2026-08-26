from __future__ import annotations
import os
import time

def run_worker(store_path, worker_id, mode):
    # Tiny process-level harness used by the chaos integration tests.
    # The parent process owns recovery and persistent state.
    with open(store_path, "a", encoding="utf-8") as f:
        f.write(f"CLAIM {worker_id}\n")
        f.flush()
        os.fsync(f.fileno())

        if mode == "crash_after_claim":
            os._exit(17)

        f.write(f"HEARTBEAT {worker_id}\n")
        f.flush()
        os.fsync(f.fileno())

        if mode == "crash_after_heartbeat":
            os._exit(18)

        f.write(f"COMPLETE {worker_id}\n")
        f.flush()
        os.fsync(f.fileno())
