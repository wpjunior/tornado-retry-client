import logging

from tornado.ioloop import IOLoop
from tornado import gen
from tornado_retry_client import RetryClient
from tornado_retry_client import http_retry
from tornado.httpclient import AsyncHTTPClient

http_client = AsyncHTTPClient()
retry_client = RetryClient(http_client, max_retries=2)


@gen.coroutine
def do_my_request():
    try:
        response = yield http_retry(http_client, 'http://httpstat.us/500')
        print "final: %s" % response.body
    except Exception, e:
        logging.exception(e)
    else:
        print('request done!')
    IOLoop.current().stop()

if __name__ == '__main__':
    IOLoop.current().spawn_callback(do_my_request)
    IOLoop.current().start()
