[![Build Status](https://secure.travis-ci.org/wpjunior/tornado-retry-client.png)](http://travis-ci.org/wpjunior/tornado-retry-client)
[![PyPI version](https://badge.fury.io/py/tornado-retry-client.svg)](https://badge.fury.io/py/tornado-retry-client)

# Tornado Retry Client
Simple retry tornado http client that support [exponential retries with backoff](http://dthain.blogspot.com/2009/02/exponential-backoff-in-distributed.html)!

## Install

with pip:

```bash
pip install tornado-retry-client
```

## Usage
```python
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado_retry_client import http_retry

http_client = AsyncHTTPClient()

@gen.coroutine
def do_my_request()
    try:
        response = yield http_retry(http_client, 'http://globo.com', attempts=2)
    except HTTPError:
        pass # My request failed after 2 retries

# OR

from tornado_retry_client import RetryClient

retry_client = RetryClient(
    retry_attempts=3,
    retry_start_timeout=0.5,
    retry_max_timeout=10,
    retry_factor=2,
)

@gen.coroutine
def do_my_request()
    try:
        response = yield retry_client.fetch('http://globo.com')
    except HTTPError:
        pass # My request failed after 2 retries
```

## Development

With empty virtualenv for this project, run this command:
```bash
make setup
```

and run all tests =)
```bash
make test
```

## Contributing
Fork, patch, test, and send a pull request.
