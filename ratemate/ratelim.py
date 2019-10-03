import multiprocessing
import time
from datetime import datetime, timedelta


class RateLimit:
    def __init__(self, max_count=1, per=1, greedy=False):
        self.greedy = greedy

        # if self.greedy:
        self._t_batch_start = multiprocessing.Value("d")
        self._batch_count = multiprocessing.Value("I")
        self._batch_count.value = 0

        # (utc) time of previous call, stored as unix timestamp (float)
        self._t_last_call = multiprocessing.Value("d")

        # number of calls
        self._count = multiprocessing.Value("I")
        self._count.value = 0

        # minimum required interval between calls
        self.max_count = max_count
        self.per = per
        self.per_timedelta = timedelta(seconds=self.per)

        # no more than max_rate calls should happen per second
        self.max_rate = max_count / per

        # to stay at the required rate, there should be at least this interval between calls
        self.min_interval = per / max_count

        self.min_interval_timedelta = timedelta(seconds=self.min_interval)

    def sleep(self, secs):
        time.sleep(secs)

    def count(self):
        return self._count.value

    def wait(self):
        with self._count.get_lock(), self._t_last_call.get_lock(), self._t_batch_start.get_lock(), self._batch_count.get_lock():
            prev_call_unix = self._t_last_call.value

            if prev_call_unix:
                t_prev_call = datetime.fromtimestamp(prev_call_unix)
            else:
                t_prev_call = None

            prev_count = self._count.value

            new_count = prev_count + 1
            self._count.value = new_count

            wait_secs = 0.0

            if prev_count > 0:
                wait_until = None

                if self.greedy:
                    batch_count = self._batch_count.value
                    new_batch_count = batch_count + 1

                    if new_batch_count >= self.max_count:
                        new_batch_count = 0

                        t_batch_start = self._t_batch_start.value
                        t_batch_start = datetime.fromtimestamp(t_batch_start)
                        wait_until = t_batch_start + timedelta(seconds=self.per)

                    self._batch_count.value = new_batch_count
                else:
                    wait_until = t_prev_call + timedelta(seconds=self.min_interval)

                if wait_until is not None:
                    wait_interval = wait_until - datetime.utcnow()
                    wait_secs = wait_interval.total_seconds()

                    if wait_secs > 0:
                        self.sleep(wait_secs)

            self._t_last_call.value = datetime.utcnow().timestamp()

            if self.greedy:
                batch_start_unset = self._t_batch_start.value is None
                new_batch_started = self._batch_count.value == 0

                if batch_start_unset or new_batch_started:
                    self._t_batch_start.value = self._t_last_call.value
            return wait_secs
