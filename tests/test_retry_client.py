# -*- coding: utf-8 -*-

import socket

from mock import MagicMock

from tornado import gen
from tornado.httpclient import HTTPError
from tornado.testing import AsyncTestCase, gen_test
from tornado.httpclient import AsyncHTTPClient
from tornado_retry_client import RetryClient


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

    def _generate_exception(self):
        gen_fetch = gen.Future()
        gen_fetch.set_exception(Exception('Generic exception'))

        self.http_client.fetch.return_value = gen_fetch

    def test_with_default_http_client(self):
        self.assertEqual(
            RetryClient().http_client,
            AsyncHTTPClient()
        )

    @gen_test
    def test_socket_error_with_retry(self):
        self._generate_fetch_socket_error()
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        request = MagicMock()

        with self.assertRaises(socket.error) as cm:
            yield self.retry_client.fetch(request)

        self.assertEqual(cm.exception.args[0], 71)
        self.assertEqual(cm.exception.args[1], 'A socket error')

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

        request = MagicMock()

        with self.assertRaises(HTTPError) as cm:
            yield self.retry_client.fetch(request)

        self.assertEqual(cm.exception.code, 422)
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 1)

    @gen_test
    def test_http_error_with_retry2(self):
        self._generate_fetch_http_error(500)
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        request = MagicMock()

        with self.assertRaises(HTTPError) as cm:
            yield self.retry_client.fetch(request)

        self.assertEqual(cm.exception.code, 500)
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 5)

    @gen_test
    def test_exception(self):
        self._generate_exception()
        self.retry_client.max_retries = 5
        self.retry_client.retry_start_timeout = 0  # 0 ** 2 = 0

        request = MagicMock()

        with self.assertRaises(Exception) as cm:
            yield self.retry_client.fetch(request)

        self.assertEqual(cm.exception.args[0], 'Generic exception')
        self.assertEqual(self.retry_client.http_client.fetch.call_count, 5)
