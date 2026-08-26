import os
import subprocess
import sys
from pathlib import Path


def run_worker(root, state, worker, mode):
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root)
    code=(
        "from packages.jobs.chaos_worker import run_worker;"
        f"run_worker({str(state)!r},{worker!r},{mode!r})"
    )
    return subprocess.run([sys.executable,"-c",code],env=env)


def events(state):
    return state.read_text(encoding="utf-8").splitlines()


def test_process_dies_after_claim_before_heartbeat(tmp_path):
    state=tmp_path/"state.log"
    result=run_worker(Path(__file__).parents[1],state,"old","crash_after_claim")
    assert result.returncode==17
    assert events(state)==["CLAIM old"]


def test_process_dies_after_heartbeat_before_completion(tmp_path):
    state=tmp_path/"state.log"
    result=run_worker(Path(__file__).parents[1],state,"old","crash_after_heartbeat")
    assert result.returncode==18
    assert events(state)==["CLAIM old","HEARTBEAT old"]


def test_restarted_process_can_finish_after_old_process_crash(tmp_path):
    state=tmp_path/"state.log"
    root=Path(__file__).parents[1]

    crashed=run_worker(root,state,"old","crash_after_claim")
    assert crashed.returncode==17

    restarted=run_worker(root,state,"new","complete")
    assert restarted.returncode==0
    assert events(state)==[
        "CLAIM old",
        "CLAIM new",
        "HEARTBEAT new",
        "COMPLETE new",
    ]


def test_process_exit_codes_are_nonzero_for_injected_crashes(tmp_path):
    state=tmp_path/"state.log"
    for mode,code in [("crash_after_claim",17),("crash_after_heartbeat",18)]:
        state.unlink(missing_ok=True)
        result=run_worker(Path(__file__).parents[1],state,"worker",mode)
        assert result.returncode==code
