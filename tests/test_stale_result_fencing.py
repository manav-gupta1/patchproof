import pytest
from packages.jobs.result_fencing import ResultFence, StaleResultRejected


class JobStore:
    def __init__(self):
        self.owner = "new"
        self.completed = None

    def succeed(self, job_id, worker_id, result):
        if worker_id != self.owner or self.completed is not None:
            return False
        self.completed = result
        return True


def test_stale_worker_result_is_rejected():
    store=JobStore()
    fence=ResultFence(store)
    with pytest.raises(StaleResultRejected):
        fence.commit("job","old",{"value":"old-result"})
    assert store.completed is None


def test_current_owner_can_commit_once():
    store=JobStore()
    fence=ResultFence(store)
    assert fence.commit("job","new",{"value":"new-result"})["value"]=="new-result"
    with pytest.raises(StaleResultRejected):
        fence.commit("job","new",{"value":"duplicate"})


def test_stale_result_cannot_overwrite_new_result():
    store=JobStore()
    fence=ResultFence(store)
    fence.commit("job","new",{"value":"authoritative"})
    with pytest.raises(StaleResultRejected):
        fence.commit("job","old",{"value":"stale"})
    assert store.completed == {"value":"authoritative"}
