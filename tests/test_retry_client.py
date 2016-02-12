# -*- coding: utf-8 -*-

from mock import patch

import tornado.httpclient
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.httpclient import AsyncHTTPClient
from tornado_retry_client import RetryClient

from tests import app


class TestRetryClient(AsyncHTTPTestCase):

    def setUp(self):
        super(TestRetryClient, self).setUp()
        self.retry_client = RetryClient(
            self.http_client,
            max_retries=5,
            retry_start_timeout=0
        )

    def get_app(self):
        return app.make_app()

    def test_with_default_http_client(self):
        self.assertEqual(
            RetryClient().http_client,
            AsyncHTTPClient()
        )

    @gen_test
    def test_socket_error_with_retry(self):
        self.retry_client.http_client = tornado.httpclient.AsyncHTTPClient(
            force_instance=True,
            defaults=dict(request_timeout=.1)
        )

        with patch.object(
            self.retry_client.http_client,
            'fetch',
            wraps=self.retry_client.http_client.fetch
        ) as fetch_mock:
            with self.assertRaises(tornado.httpclient.HTTPError) as cm:
                yield self.retry_client.fetch(self.get_url('/timeout'))

        self.assertEqual(cm.exception.args[0], 599)
        self.assertEqual(cm.exception.args[1], 'Timeout')

        self.assertEqual(fetch_mock.call_count, 5)

    @gen_test
    def test_http_success(self):
        response = yield self.retry_client.fetch(self.get_url('/'))
        self.assertEqual(response.code, 200)

    @gen_test
    def test_http_error_with_retry(self):
        self.retry_client.http_client = tornado.httpclient.AsyncHTTPClient(
            force_instance=True,
            defaults=dict(request_timeout=.1)
        )

        with patch.object(
            self.retry_client.http_client,
            'fetch',
            wraps=self.retry_client.http_client.fetch
        ) as fetch_mock:
            with self.assertRaises(tornado.httpclient.HTTPError) as cm:
                yield self.retry_client.fetch(self.get_url('/error_no_retry'))

        self.assertEqual(cm.exception.code, 422)
        self.assertEqual(fetch_mock.call_count, 1)

    @gen_test
    def test_http_error_with_retry2(self):
        self.retry_client.http_client = tornado.httpclient.AsyncHTTPClient(
            force_instance=True,
            defaults=dict(request_timeout=.1)
        )

        with patch.object(
            self.retry_client.http_client,
            'fetch',
            wraps=self.retry_client.http_client.fetch
        ) as fetch_mock:
            with self.assertRaises(tornado.httpclient.HTTPError) as cm:
                yield self.retry_client.fetch(self.get_url('/error'))

        self.assertEqual(cm.exception.code, 500)
        self.assertEqual(fetch_mock.call_count, 5)

    @gen_test
    def test_custom_http_client_error(self):
        class TokenError(Exception):
            pass

        class MyHttpClient(object):
            def __init__(self):
                self.count = 0

            def fetch(self, *args, **kwargs):
                future = tornado.gen.Future()
                future.set_exception(TokenError('my token error'))
                self.count += 1
                return future

        http_client = MyHttpClient()

        self.retry_client.http_client = http_client
        self.retry_client.retry_exceptions = (TokenError,)

        with self.assertRaises(TokenError):
            yield self.retry_client.fetch(
                self.get_url('/'),
                retry_wait=.1,
                retry_exceptions=(TokenError,)
            )

        self.assertEqual(http_client.count, 5)
