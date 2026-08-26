from datetime import datetime, timedelta, timezone
import threading

from packages.jobs.lease_race import LeaseRaceGuard


def test_renew_before_expiry_extends_commit_window():
    t=datetime.now(timezone.utc)
    g=LeaseRaceGuard("worker-a", t+timedelta(seconds=1))
    assert g.renew("worker-a", t+timedelta(milliseconds=500), timedelta(seconds=5)).renewed
    assert g.commit("worker-a", t+timedelta(seconds=2)) is True


def test_renew_after_expiry_cannot_resurrect_lease():
    t=datetime.now(timezone.utc)
    g=LeaseRaceGuard("worker-a", t+timedelta(seconds=1))
    assert g.renew("worker-a", t+timedelta(seconds=2), timedelta(seconds=5)).renewed is False
    assert g.commit("worker-a", t+timedelta(seconds=2)) is False


def test_stale_worker_cannot_commit_after_expiry():
    t=datetime.now(timezone.utc)
    g=LeaseRaceGuard("worker-a", t+timedelta(seconds=1))
    assert g.commit("worker-a", t+timedelta(seconds=2)) is False


def test_concurrent_renew_and_commit_has_one_terminal_outcome():
    t=datetime.now(timezone.utc)
    g=LeaseRaceGuard("worker-a", t+timedelta(seconds=1))
    barrier=threading.Barrier(2)
    outcomes=[]

    def renew():
        barrier.wait()
        outcomes.append(("renew", g.renew(
            "worker-a", t+timedelta(milliseconds=900), timedelta(seconds=5)
        ).renewed))

    def commit():
        barrier.wait()
        outcomes.append(("commit", g.commit("worker-a", t+timedelta(seconds=2))))

    a=threading.Thread(target=renew)
    b=threading.Thread(target=commit)
    a.start(); b.start(); a.join(); b.join()

    # Depending on serialization, renewal may extend the window before commit,
    # or commit may win first. The state must never become completed and then
    # be renewed successfully.
    assert sum(x[1] for x in outcomes) >= 1
    assert not (g.completed and g.renew("worker-a", t+timedelta(seconds=3),
                                        timedelta(seconds=1)).renewed)


def test_commit_is_terminal_and_renewal_cannot_follow():
    t=datetime.now(timezone.utc)
    g=LeaseRaceGuard("worker-a", t+timedelta(seconds=10))
    assert g.commit("worker-a", t+timedelta(seconds=1))
    assert not g.renew("worker-a", t+timedelta(seconds=2), timedelta(seconds=5)).renewed
