# ratemate

There's a bunch of python rate limiting modules out there, but they all seem to suffer from similar problems:

- Weird APIs, usually inflexible decorators that you need to wrap your calls in
- Lack of `multiprocessing` support (eg, two processes will be unaware of each other, and thus double the intended rate)
- Unnecessary coupling to other libraries

`ratemate`, meanwhile, gives you a simple `RateLimit` object that avoids all these problems.

It works like this. Declare a `RateLimit` as follows:

    from ratemate import RateLimit

    rate_limit = RateLimit(max_count=2, per=5)  # 2 requests per 5 seconds

Then call `.wait()` appropriately when you need to limit the rate.

For instance, here's an example when creating multiple threads with `concurrent.futures`. First the original rate-unlimited code:

```python

from concurrent.futures import ThreadPoolExecutor, as_completed


def task(n):
    print(f"  task {n} called")
    return n

futures = []

with ThreadPoolExecutor() as executor:
    for i in range(20):
        future = executor.submit(task, i)
        futures.append(future)

    for completed in as_completed(futures):
        result = completed.result()
        print('completed')
```

Add rate-limiting simply by adding a wait at the appropriate time, either at task creation:

```python
for i in range(20):
    rate_limit.wait()  # wait before creating the task
    future = executor.submit(task, i)
    futures.append(future)
```

Or at the start of the task itself:

```python
def task(n):
    waited_time = rate_limit.wait()  # wait at start of task
    print(f"  task {n}: waited for {waited_time} secs")
    return n
```

Because `ratemate` uses multi-process-aware shared memory to track its state, you can also use `ProcessPoolExecutor` and everything will still work nicely.


## Greedy mode

The default (aka non-greedy aka patient) rate limiting mode spaces out calls evenly. First instance, max_count=10 and per=60 will result in one call every 6 seconds.

You may instead wish for calls to happen as fast as possible, only slowing down if the limit would be exceeded. Enable this with greedy=True, eg:

```
rate_limit = RateLimit(max_count=20, per=60, greedy=True)
```

## Further enhancements

Rate limit coordination between truly independent processes (not just subprocesses), possibly using Python 3.8's new shared memory or Redis or PostgreSQL or whatever.

