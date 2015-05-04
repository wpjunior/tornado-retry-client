# -*- coding: utf-8 -*-

import socket

from mock import MagicMock

from tornado import gen
from tornado.httpclient import HTTPError
from tornado.testing import AsyncTestCase, gen_test

from tornado_retry_client import RetryClient, FailedRequest


class TestRetryClient(AsyncTestCase):
    def setUp(self):
        super(TestRetryClient, self).setUp()

        self.http_client = MagicMock()
        self.retry_client = RetryClient(self.http_client)

    def _generate_fetch_http_error(self, code=422):
        response = MagicMock(code=code, body='A Server Error')
        gen_fetch = gen.Future()
        gen_fetch.set_exception(HTTPError(code=code, response=response))

        self.http_client.fetch.return_value = gen_fetch

    def _generate_fetch_socket_error(self):
        gen_fetch = gen.Future()
        gen_fetch.set_exception(socket.error(71, 'A socket error'))

        self.http_client.fetch.return_value = gen_fetch

    @gen_test
    def test_socket_error_with_retry(self):
        self._generate_fetch_socket_error()
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        raised_error = False
        request = MagicMock()

        try:
            yield self.retry_client.fetch(request)
        except FailedRequest as error:
            self.assertEqual(error.args[0], 'Max request retries')
            raised_error = True

        self.assertTrue(raised_error)
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 5)

    @gen_test
    def test_http_success(self):
        response = MagicMock(code=200, body='Result')
        gen_fetch = gen.Future()
        gen_fetch.set_result(response)

        self.http_client.fetch.return_value = gen_fetch
        request = MagicMock()

        expected_response = yield self.retry_client.fetch(request)
        self.assertEqual(expected_response, response)

    @gen_test
    def test_http_error_with_retry(self):
        self._generate_fetch_http_error(422)
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        raised_error = False
        request = MagicMock()

        try:
            yield self.retry_client.fetch(request)
        except FailedRequest as error:
            self.assertEqual(error.args[0], 'Invalid response')
            raised_error = True

        self.assertTrue(raised_error)
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 1)

    @gen_test
    def test_http_error_with_retry2(self):
        self._generate_fetch_http_error(500)
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        raised_error = False
        request = MagicMock()

        try:
            yield self.retry_client.fetch(request)
        except FailedRequest as error:
            self.assertEqual(error.args[0], 'Max request retries')
            raised_error = True

        self.assertTrue(raised_error)
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 5)
