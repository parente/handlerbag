'''Says hello world.'''
# tornado
import tornado.web

class HelloHandler(tornado.web.RequestHandler):
    def initialize(self, **options):
        self.options = options

    def get(self, *args, **kwargs):
        self.write(self.options['greeting'])

def get_handler_map(app, webroot, options):
    return [(webroot+'hello/?', HelloHandler, options)]
    
def get_default_options(app):
    return {'greeting' : 'Hello world!'}