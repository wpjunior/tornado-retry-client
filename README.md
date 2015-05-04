[![Build Status](https://secure.travis-ci.org/wpjunior/tornado-retry-client.png)](http://travis-ci.org/wpjunior/tornado-retry-client)

Simple Example
--------------

```python
from tornado_retry_client import RetryClient, FailedRequest
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

http_client = AsyncHTTPClient()
retry_client = RetryClient(http_client, max_retries=2)

@gen.coroutine
def do_my_request()
    try:
        request = HTTPRequest(url='http://globo.com')
        response = yield retry_client.fetch(request)
    except FailedRequest:
        pass # My request failed after 2 retries
```
