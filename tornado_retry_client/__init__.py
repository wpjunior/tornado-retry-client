# -*- coding: utf-8 -*-

__all__ = ('RetryClient', 'FailedRequest')

import os
import logging
import socket

from tornado import gen
from tornado.httpclient import HTTPError

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


class FailedRequest(RequestException):
    pass


class RetryClient(object):
    RETRY_HTTP_ERROR_CODES = (500, 502, 503, 504)

    def __init__(self, http_client, max_retries=MAX_RETRIES,
                 max_retry_timeout=MAX_RETRY_TIMEOUT,
                 retry_start_timeout=RETRY_START_TIMEOUT):

        self.http_client = http_client
        self.logger = logging.getLogger('RetryClient')

        self.max_retries = max_retries
        self.max_retry_timeout = max_retry_timeout
        self.retry_start_timeout = retry_start_timeout

    @gen.coroutine
    def _do_fetch(self, request, attempt=1):
        try:
            response = yield self.http_client.fetch(request)
        except HTTPError as e:
            if e.response:
                self.logger.error(
                    '[attempt: %d] request failed: %s', attempt,
                    e.response.body)

                if e.response.code in self.RETRY_HTTP_ERROR_CODES:
                    raise RetryRequest(reason=e)

            else:
                self.logger.error('[attempt: %d] request failed'
                                  ' [without response]', attempt)
                raise RetryRequest(reason=e)

            raise StopRequest(reason=e)

        except socket.error as e:
            self.logger.error(
                'Connection error: %d -> %s', e.args[0], e.args[1])

            raise RetryRequest(reason=e)

        except Exception as e:
            self.logger.error('Generic error')
            self.logger.exception(e)

            raise RetryRequest(e)

        else:
            raise gen.Return(response)

    @gen.coroutine
    def fetch(self, request):
        attempt = 1
        retry_timeout = self.retry_start_timeout

        while True:
            try:
                response = yield self._do_fetch(request, attempt)
            except RetryRequest as e:
                attempt += 1

                if attempt > self.max_retries:
                    self.logger.error('Max request retries')
                    raise FailedRequest(reason=e.reason,
                                        message='Max request retries')

                self.logger.warn('Trying again in %s seconds', retry_timeout)

                yield gen.sleep(retry_timeout)
                retry_timeout *= 2
                retry_timeout = min(retry_timeout, self.max_retry_timeout)

            except StopRequest as e:
                self.logger.error('Request fail in %d attempts', attempt)
                raise FailedRequest(reason=e.reason,
                                    message='Invalid response')

            else:
                self.logger.debug('Request done!, god bless!')
                raise gen.Return(response)
