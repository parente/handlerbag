# tornado
import tornado.web

class HelloHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write('Hello world!')

def get_handler_map(webroot):
    return [(webroot+'hello/?', HelloHandler)]