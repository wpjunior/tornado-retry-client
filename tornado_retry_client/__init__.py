# -*- coding: utf-8 -*-

import os
import logging

from tornado.httpclient import AsyncHTTPClient
from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from functools import partial


START_TIMEOUT = float(
    os.environ.get("TORNADO_RETRYCLIENT_START_TIMEOUT", "0.1")
)
MAX_TIMEOUT = int(os.environ.get("TORNADO_RETRYCLIENT_MAX_TIMEOUT", "30"))
ATTEMPTS = int(os.environ.get("TORNADO_RETRYCLIENT_ATTEMPTS", "5"))
FACTOR = int(os.environ.get("TORNADO_RETRYCLIENT_FACTOR", "2"))


class RetryClient(object):
    def __init__(
        self,
        http_client=None,
        retry_attempts=ATTEMPTS,
        retry_start_timeout=START_TIMEOUT,
        retry_max_timeout=MAX_TIMEOUT,
        retry_factor=FACTOR,
        retry_for_statuses=None,
        retry_exceptions=None,
        logger=None,
    ):

        if http_client:
            self.http_client = http_client
        else:
            self.http_client = AsyncHTTPClient()

        self.retry_attempts = retry_attempts
        self.retry_max_timeout = retry_max_timeout
        self.retry_start_timeout = retry_start_timeout
        self.retry_exceptions = retry_exceptions
        self.retry_for_statuses = retry_for_statuses
        self.retry_factor = retry_factor
        self.logger = logger

    def fetch(self, request, **kwargs):
        kwargs.setdefault("retry_start_timeout", self.retry_start_timeout)
        kwargs.setdefault("attempts", self.retry_attempts)
        kwargs.setdefault("retry_exceptions", self.retry_exceptions)
        kwargs.setdefault("retry_factor", self.retry_factor)
        kwargs.setdefault("logger", self.logger)
        kwargs.setdefault("retry_for_statuses", self.retry_for_statuses)
        kwargs.setdefault("retry_max_timeout", self.retry_max_timeout)

        return http_retry(self.http_client, request, **kwargs)


def http_retry(
    client,
    request,
    raise_error=True,
    attempts=ATTEMPTS,
    retry_start_timeout=START_TIMEOUT,
    retry_max_timeout=MAX_TIMEOUT,
    retry_exceptions=None,
    retry_factor=FACTOR,
    retry_for_statuses=None,
    logger=None,
    **kwargs
):
    attempt = 0
    future = Future()
    ioloop = IOLoop.current()

    if not retry_exceptions:
        retry_exceptions = ()

    if not retry_for_statuses:
        retry_for_statuses = ()

    if not logger:
        logger = logging.getLogger("RetryClient")

    def _do_request(attempt):
        http_future = client.fetch(request, raise_error=False, **kwargs)
        http_future.add_done_callback(partial(handle_future, attempt))

    def handle_future(attempt, future_response):
        attempt += 1
        exception = future_response.exception()
        if exception:
            return handle_exception(attempt, exception)

        handle_response(attempt, future_response.result())

    def check_code(code):
        return code >= 500 and code <= 599 or code in retry_for_statuses

    def exponential_timeout(attempt):
        timeout = retry_start_timeout * (retry_factor ** (attempt - 1))
        return min(timeout, retry_max_timeout)

    def handle_response(attempt, result):
        if result.error and attempt < attempts and check_code(result.code):
            retry_wait = exponential_timeout(attempt)
            logger.warning(
                u"attempt: %d, %s request failed: %s, body: %s",
                attempt,
                result.effective_url,
                result.error,
                repr(result.body),
            )
            return ioloop.call_later(retry_wait, lambda: _do_request(attempt))

        if raise_error and result.error:
            return future.set_exception(result.error)

        future.set_result(result)

    def handle_exception(attempt, exception):
        retry_wait = exponential_timeout(attempt)
        logger.warning(
            u"attempt: %d, request failed with exception: %s", attempt, exception
        )
        if isinstance(exception, retry_exceptions) and attempt < attempts:
            return ioloop.call_later(retry_wait, lambda: _do_request(attempt))

        return future.set_exception(exception)

    _do_request(attempt)
    return future
