# -*- coding: utf-8 -*-

import os
import logging

from tornado.httpclient import AsyncHTTPClient
from tornado.concurrent import TracebackFuture
from tornado.ioloop import IOLoop
from functools import partial


RETRY_START_TIMEOUT = int(os.environ.get('RETRY_START_TIMEOUT', '1'))
MAX_RETRY_TIMEOUT = int(os.environ.get('MAX_RETRY_TIMEOUT', '30'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '30'))


class RetryClient(object):

    def __init__(self, http_client=None, max_retries=MAX_RETRIES,
                 max_retry_timeout=MAX_RETRY_TIMEOUT,
                 retry_start_timeout=RETRY_START_TIMEOUT):

        if http_client:
            self.http_client = http_client
        else:
            self.http_client = AsyncHTTPClient()

        self.logger = logging.getLogger('RetryClient')

        self.max_retries = max_retries
        self.max_retry_timeout = max_retry_timeout
        self.retry_start_timeout = retry_start_timeout

    def fetch(self, request, *args, **kwargs):
        return http_retry(
            self.http_client,
            request,
            retry_wait=self.retry_start_timeout,
            attempts=self.max_retries
        )


def http_retry(
        client, request,
        raise_error=True, attempts=5,
        retry_wait=1, **kwargs):
    attempt = 1
    future = TracebackFuture()
    ioloop = IOLoop.current()

    def _do_request(attempt):
        http_future = client.fetch(request, raise_error=False, **kwargs)
        http_future.add_done_callback(partial(handle_response, attempt))

    def handle_response(attempt, future_response):
        attempt += 1
        result = future_response.result()
        if result.error:
            logging.error(
                u'attempt: %d, %s request failed: %s, body: %s',
                attempt, result.effective_url, result.error, result.body)

            if attempt <= attempts and\
               result.code >= 500 and\
               result.code <= 599:
                return ioloop.call_later(
                    retry_wait, lambda: _do_request(attempt))

        if raise_error and result.error:
            return future.set_exception(result.error)

        future.set_result(result)

    _do_request(attempt)
    return future
