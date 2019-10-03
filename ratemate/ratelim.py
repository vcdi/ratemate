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

    @property
    def count(self):
        return self._count.value

    @count.setter
    def count(self, value):
        self._count.value = value

    @property
    def batch_count(self):
        return self._batch_count.value

    @batch_count.setter
    def batch_count(self, value):
        self._batch_count.value = value

    @property
    def dt_previous_call(self):
        prev_call_unix = self._t_last_call.value

        if prev_call_unix:
            return datetime.fromtimestamp(prev_call_unix)

    @dt_previous_call.setter
    def dt_previous_call(self, value):
        self._t_last_call.value = value

    def is_first_call(self):
        return self.count == 0

    def wait_until(self, dt_wait_until):
        wait_interval = dt_wait_until - datetime.utcnow()
        wait_secs = wait_interval.total_seconds()

        if wait_secs > 0:
            self.sleep(wait_secs)
            return wait_secs
        return 0.0

    @property
    def dt_batch_start(self):
        _dt_batch_start = self._t_batch_start.value

        if _dt_batch_start:
            return datetime.fromtimestamp(_dt_batch_start)

    @dt_batch_start.setter
    def dt_batch_start(self, value):
        self._t_batch_start.value = value

    def wait(self):
        with self._count.get_lock(), self._t_last_call.get_lock(), self._t_batch_start.get_lock(), self._batch_count.get_lock():

            dt_previous_call = self.dt_previous_call

            wait_secs = 0.0

            if not self.is_first_call():
                if self.greedy:
                    self.batch_count += 1

                    if self.batch_count >= self.max_count:
                        self.batch_count = 0

                        dt_wait_until = self.dt_batch_start + self.per_timedelta
                        wait_secs = self.wait_until(dt_wait_until)
                else:
                    dt_wait_until = dt_previous_call + self.min_interval_timedelta
                    wait_secs = self.wait_until(dt_wait_until)

            self.count += 1

            now_timestamp = datetime.utcnow().timestamp()

            self.dt_previous_call = now_timestamp

            if self.greedy and self.batch_count:
                self.dt_batch_start = now_timestamp

            return wait_secs
