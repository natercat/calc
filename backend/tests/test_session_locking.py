import threading
import time

from app.session_store import _get_lock, create_session, session_lock


class TestLockIdentity:
    def test_same_session_id_returns_the_same_lock_object(self):
        session_id = create_session()
        assert _get_lock(session_id) is _get_lock(session_id)

    def test_different_session_ids_get_independent_locks(self):
        a = create_session()
        b = create_session()
        assert _get_lock(a) is not _get_lock(b)


class TestSessionLockMutualExclusion:
    def test_session_lock_prevents_a_lost_update(self):
        # Classic read-sleep-write race: without mutual exclusion, threads
        # can all read the same stale value before any of them writes back,
        # silently losing updates. A sleep between read and write widens the
        # race window so this is deterministic, not timing-dependent luck.
        session_id = create_session()
        shared = {"counter": 0}
        recorded = []
        recorded_lock = threading.Lock()

        def worker():
            with session_lock(session_id):
                current = shared["counter"]
                time.sleep(0.02)
                shared["counter"] = current + 1
                with recorded_lock:
                    recorded.append(shared["counter"])

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert shared["counter"] == 8
        assert sorted(recorded) == list(range(1, 9))

    def test_without_synchronization_the_same_race_loses_updates(self):
        # Demonstrates the race the test above is actually protecting
        # against: the identical read-sleep-write pattern with no lock at
        # all reliably loses updates under the same artificial delay.
        shared = {"counter": 0}

        def worker():
            current = shared["counter"]
            time.sleep(0.02)
            shared["counter"] = current + 1

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert shared["counter"] < 8

    def test_two_sessions_do_not_serialize_against_each_other(self):
        # Locking must be per-session, not global -- two different sessions'
        # critical sections should be able to run concurrently.
        session_a = create_session()
        session_b = create_session()
        started = threading.Event()
        overlapped = threading.Event()

        def hold_a():
            with session_lock(session_a):
                started.set()
                time.sleep(0.1)

        def try_b():
            started.wait()
            with session_lock(session_b):
                overlapped.set()

        t1 = threading.Thread(target=hold_a)
        t2 = threading.Thread(target=try_b)
        t1.start()
        t2.start()
        t2.join(timeout=1)
        t1.join(timeout=1)

        assert overlapped.is_set(), "session_b's lock should not wait on session_a's"
