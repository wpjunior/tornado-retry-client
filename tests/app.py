import tornado.web


COUNTER = 0


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class ErrorHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(500)


class NonRetryableErrorHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(422, 'Unprocessable Entity')


class TimeoutHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        yield tornado.gen.sleep(10)


class ErrorSometimesHandler(tornado.web.RequestHandler):
    def get(self):
        global COUNTER
        COUNTER += 1
        if COUNTER == 5:
            self.write("Hello, world")
            return self.set_status(200)
        self.set_status(500)


def make_app():
    global COUNTER
    COUNTER = 0
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/error", ErrorHandler),
        (r"/error_sometimes", ErrorSometimesHandler),
        (r"/error_no_retry", NonRetryableErrorHandler),
        (r"/timeout", TimeoutHandler),
    ])
