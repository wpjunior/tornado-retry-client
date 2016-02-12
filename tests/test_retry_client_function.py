import tornado.web
import tornado.gen
from tornado.testing import AsyncHTTPTestCase
from tornado.testing import gen_test
import tornado.httpclient

from tests import app

import tornado_retry_client


class TestRetryFunction(AsyncHTTPTestCase):
    def get_app(self):
        return app.make_app()

    @gen_test
    def test_success(self):
        response = yield tornado_retry_client.http_retry(
            self.get_http_client(), self.get_url('/')
        )
        self.assertEqual(response.code, 200)

    @gen_test
    def test_success_after_retry(self):
        response = yield tornado_retry_client.http_retry(
            self.get_http_client(), self.get_url('/error_sometimes'),
            retry_wait=.1
        )
        self.assertEqual(response.code, 200)
        self.assertEqual(app.COUNTER, 5)

    @gen_test
    def test_error(self):
        response = yield tornado_retry_client.http_retry(
            self.get_http_client(), self.get_url('/error'),
            retry_wait=.1,
            raise_error=False
        )
        self.assertEqual(response.code, 500)

    @gen_test
    def test_timeout_error(self):
        client = tornado.httpclient.AsyncHTTPClient(
            force_instance=True,
            defaults=dict(request_timeout=.1)
        )
        response = yield tornado_retry_client.http_retry(
            client, self.get_url('/timeout'),
            retry_wait=.1,
            raise_error=False
        )
        self.assertEqual(response.code, 599)

    @gen_test
    def test_raise_error(self):
        with self.assertRaises(tornado.httpclient.HTTPError):
            yield tornado_retry_client.http_retry(
                self.get_http_client(), self.get_url('/error'),
                retry_wait=.1
            )

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

        with self.assertRaises(TokenError):
            yield tornado_retry_client.http_retry(
                http_client, self.get_url('/'),
                retry_wait=.1,
                retry_exceptions=(TokenError,)
            )

        self.assertEqual(http_client.count, 5)
