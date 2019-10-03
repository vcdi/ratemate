from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from ratemate import RateLimit

rate_limit = RateLimit(max_count=10, per=1, greedy=False)
rate_limit_greedy = RateLimit(max_count=10, per=1, greedy=True)


def task(n):
    rate_wait = rate_limit.wait()
    print(f"  task {n}: waited for {rate_wait} secs")
    return n


def greedy_task(n):
    rate_wait = rate_limit_greedy.wait()
    print(f"  task {n}: waited for {rate_wait} secs")
    return n


def test_ratelim_basic():
    rate_limit = RateLimit(max_count=10, per=1)

    def task(n):
        return n

    for i in range(20):
        rate_limit.wait()
        task(i)


def test_ratelim_concurrent():
    futures = []

    with ThreadPoolExecutor() as executor:
        for i in range(20):
            future = executor.submit(task, i)
            futures.append(future)

        for completed in as_completed(futures):
            result = completed.result()
            print(f"completed: {result}")

    assert rate_limit.count() == 20


def test_ratelim_greedy():
    futures = []

    with ProcessPoolExecutor() as executor:
        for i in range(20):
            future = executor.submit(greedy_task, i)
            futures.append(future)

        for completed in as_completed(futures):
            result = completed.result()
            print(f"completed: {result}")

    assert rate_limit_greedy.count() == 20
