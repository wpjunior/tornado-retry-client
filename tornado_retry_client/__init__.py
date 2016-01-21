# -*- coding: utf-8 -*-

import os
import logging
import socket

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest

__all__ = ('RetryClient',)

RETRY_START_TIMEOUT = int(os.environ.get('RETRY_START_TIMEOUT', '1'))
MAX_RETRY_TIMEOUT = int(os.environ.get('MAX_RETRY_TIMEOUT', '30'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '30'))


class RequestException(Exception):

    def __init__(self, reason, message=''):
        super(RequestException, self).__init__(message)
        self.reason = reason


class RetryRequest(RequestException):
    pass


class StopRequest(RequestException):
    pass


class RetryClient(object):
    RETRY_HTTP_ERROR_CODES = (500, 502, 503, 504)

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

    @gen.coroutine
    def _do_fetch(self, request, args, kwargs, attempt=1):
        if isinstance(request, HTTPRequest):
            url = request.url
        else:
            url = request

        try:
            response = yield self.http_client.fetch(request, *args, **kwargs)
        except HTTPError as e:
            if e.response:
                body = e.response.body
                if hasattr(body, 'decode'):
                    body = body.decode('utf-8')
                self.logger.error(u'attempt: %d, %s request failed: %s',
                                  attempt, url, body)

                if e.response.code in self.RETRY_HTTP_ERROR_CODES:
                    raise RetryRequest(reason=e)

            else:
                self.logger.error('attempt: %d, %s request failed'
                                  ' [without response]', attempt, url)
                raise RetryRequest(reason=e)

            raise StopRequest(reason=e)

        except socket.error as e:
            self.logger.error(
                'attempt: %d, %s connection error: %s', attempt, url,
                e)

            raise RetryRequest(reason=e)

        except Exception as e:
            self.logger.error('Generic error')
            self.logger.exception(e)

            raise RetryRequest(e)

        else:
            raise gen.Return(response)

    @gen.coroutine
    def fetch(self, request, *args, **kwargs):
        attempt = 1
        retry_timeout = self.retry_start_timeout

        while True:
            try:
                response = yield self._do_fetch(request, args, kwargs, attempt)
            except RetryRequest as e:
                attempt += 1

                if attempt > self.max_retries:
                    self.logger.error(
                        'attempt: %d, max request retries', attempt)
                    raise e.reason

                self.logger.warn('Trying again in %s seconds', retry_timeout)

                yield gen.sleep(retry_timeout)
                retry_timeout *= 2
                retry_timeout = min(retry_timeout, self.max_retry_timeout)

            except StopRequest as e:
                self.logger.error('Request fail in %d attempts', attempt)
                raise e.reason

            else:
                self.logger.debug('Request done!, god bless!')
                raise gen.Return(response)
