
import pytest
from unittest.mock import Mock
from retry import Retry

def test_success_first_attempt():
    fn = Mock(return_value="Success")

    retry = Retry(maxAttempts=3)

    result = retry.execute(fn)

    assert result == "Success"
    assert fn.call_count == 1

def test_success_after_failures():
    fn = Mock(
        side_effect=[
            TimeoutError("Server unavailable"),
            TimeoutError("Server unavailable"),
            "Success"
        ]
    )

    delays = []

    retry = Retry(
        maxAttempts=3,
        strategy="constant",
        retryOn=(TimeoutError,),
        baseDelay=1,
        sleepFn=delays.append
    )

    result = retry.execute(fn)

    assert result == "Success"
    assert fn.call_count == 3
    assert delays == [1, 1]

def test_max_attempts():
    fn = Mock(side_effect=TimeoutError("Server unavailable"))

    delays = []

    retry = Retry(
        maxAttempts=4,
        strategy="constant",
        retryOn=(TimeoutError,),
        baseDelay=2,
        sleepFn=delays.append
    )

    with pytest.raises(TimeoutError):
        retry.execute(fn)

    assert fn.call_count == 4
    assert sum(delays) == 6
    assert delays == [2, 2, 2]

def test_exponential_delay():
    fn = Mock(side_effect=TimeoutError("Server unavailable"))

    delays = []

    retry = Retry(
        maxAttempts=4,
        strategy="exponential",
        retryOn=(TimeoutError,),
        baseDelay=1,
        sleepFn=delays.append
    )

    with pytest.raises(TimeoutError):
        retry.execute(fn)

    assert delays == [1, 2, 4]
    assert sum(delays) == 7

def test_non_retryable_error():
    fn = Mock(side_effect=ValueError("Invalid data"))

    delays = []

    retry = Retry(
        maxAttempts=3,
        retryOn=(TimeoutError,),
        sleepFn=delays.append
    )

    with pytest.raises(ValueError):
        retry.execute(fn)

    assert fn.call_count == 1
    assert delays == []

def test_exponential_jitter():
    fn = Mock(side_effect=TimeoutError("Server unavailable"))

    delays = []

    retry = Retry(
        maxAttempts=4,
        strategy="exponentialJitter",
        retryOn=(TimeoutError,),
        baseDelay=1,
        randomFn=lambda a, b: b / 2,
        sleepFn=delays.append
    )

    with pytest.raises(TimeoutError):
        retry.execute(fn)

    assert delays == [0.5, 1.0, 2.0]
    assert sum(delays) == 3.5

def test_retry_on_error_code():

    class ServerError(Exception):
        def __init__(self, code):
            self.code = code

    fn = Mock(
        side_effect=[
            ServerError(503),
            "Success"
        ]
    )

    retry = Retry(
        maxAttempts=3,
        retryOn=(503,),
        sleepFn=lambda delay: None
    )

    result = retry.execute(fn)

    assert result == "Success"
    assert fn.call_count == 2
