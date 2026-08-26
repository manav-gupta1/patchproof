import sqlite3
import subprocess
import sys
import os
from pathlib import Path


def run(root, db, worker, mode):
    env=os.environ.copy()
    env["PYTHONPATH"]=str(root)
    return subprocess.run(
        [sys.executable, "-m", "packages.jobs.sql_process_harness",
         str(db), worker, mode],
        env=env,
    )


def read(db):
    con=sqlite3.connect(db)
    row=con.execute(
        "SELECT status, worker_id, result FROM jobs WHERE job_id='job'"
    ).fetchone()
    con.close()
    return row


def test_real_process_crash_persists_running_state(tmp_path):
    root=Path(__file__).parents[1]
    db=tmp_path/"jobs.sqlite"

    result=run(root,db,"old","crash_after_claim")

    assert result.returncode==17
    assert read(db)==("running","old",None)


def test_restart_can_finish_persisted_job_after_recovery(tmp_path):
    root=Path(__file__).parents[1]
    db=tmp_path/"jobs.sqlite"

    crashed=run(root,db,"old","crash_after_claim")
    assert crashed.returncode==17

    # Simulate recovery of the abandoned worker in the persistent DB.
    con=sqlite3.connect(db)
    con.execute(
        "UPDATE jobs SET status='queued', worker_id=NULL "
        "WHERE job_id='job' AND status='running' AND worker_id='old'"
    )
    con.commit()
    con.close()

    restarted=run(root,db,"new","complete")
    assert restarted.returncode==0
    assert read(db)==("succeeded",None,"authoritative")


def test_old_worker_cannot_complete_after_new_worker_owns_job(tmp_path):
    root=Path(__file__).parents[1]
    db=tmp_path/"jobs.sqlite"

    assert run(root,db,"old","crash_after_claim").returncode==17

    con=sqlite3.connect(db)
    con.execute(
        "UPDATE jobs SET status='queued', worker_id=NULL WHERE job_id='job'"
    )
    con.commit()
    con.close()

    assert run(root,db,"new","complete").returncode==0
    assert read(db)==("succeeded",None,"authoritative")
