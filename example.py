import socket
from tornado.ioloop import IOLoop
from tornado import gen
from tornado_retry_client import RetryClient
from tornado_retry_client import http_retry
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

http_client = AsyncHTTPClient()
retry_client = RetryClient(http_client, max_retries=2)


@gen.coroutine
def do_my_request():
    try:
        response = yield http_retry(http_client, 'http://nao_existe.com')
        print "final: %s" % response.body
    except HTTPError as err:
        print('http error', err)
    except socket.error as err:
        print('socket error', err)

    else:
        print('request done!')

if __name__ == '__main__':
    IOLoop.current().spawn_callback(do_my_request)
    IOLoop.current().start()
