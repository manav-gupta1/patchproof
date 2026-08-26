from __future__ import annotations
import sqlite3
import sys

def init_db(path):
    con=sqlite3.connect(path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS jobs "
        "(job_id TEXT PRIMARY KEY, status TEXT NOT NULL, "
        "worker_id TEXT, result TEXT)"
    )
    con.execute(
        "INSERT OR IGNORE INTO jobs(job_id,status) VALUES('job','queued')"
    )
    con.commit()
    con.close()

def claim(path, worker):
    con=sqlite3.connect(path)
    cur=con.execute(
        "UPDATE jobs SET status='running', worker_id=? "
        "WHERE job_id='job' AND status='queued'",
        (worker,),
    )
    con.commit()
    con.close()
    return cur.rowcount == 1

def complete(path, worker, result):
    con=sqlite3.connect(path)
    cur=con.execute(
        "UPDATE jobs SET status='succeeded', worker_id=NULL, result=? "
        "WHERE job_id='job' AND status='running' AND worker_id=?",
        (result, worker),
    )
    con.commit()
    con.close()
    return cur.rowcount == 1

def main(path, worker, mode):
    init_db(path)
    if not claim(path, worker):
        return 3
    if mode == "crash_after_claim":
        return 17
    if mode == "complete":
        return 0 if complete(path, worker, "authoritative") else 4
    return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
