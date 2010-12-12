'''Cross-domain dropbox with optional GET.'''
# tornado
import tornado.web
# std lib
import os.path
import datetime
import urlparse

class XHRDropHandler(tornado.web.StaticFileHandler):
    def __init__(self, application, request, path, default_filename=None, **kwargs):
        '''Override to accept additional kwargs.'''
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.root = os.path.abspath(path) + os.path.sep
        self.default_filename = default_filename
    
    def initialize(self, **options):
        self.options = options
    
    def options(self, *args, **kwargs):
        # allow preflights from all
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Max-Age', '0')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        self.set_header('Content-Type', 'text/plain')
    
    def post(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'text/plain')
        origin = self.request.headers.get('Origin')
        urlObj = urlparse.urlsplit(origin)
        dt = datetime.datetime.now().isoformat()
        fn = '%s-%s.txt' % (urlObj.netloc.replace(':', '-'), dt)
        with file(os.path.join(self.options['path'], fn), 'w') as f:
            f.write(self.request.body)
        self.write(fn)

    def get(self, *args, **kwargs):
        if not self.options['get_enabled']:
            raise tornado.web.HTTPError(405)
        super(XHRDropHandler, self).get(*args, **kwargs)

def get_handler_map(app, webroot, **options):
    tmp = {'path' : os.path.join(app.bagPath, 'xhrdrop')}
    tmp.update(options)
    return [(webroot+'xhrdrop/?(.*)', XHRDropHandler, tmp)]

def get_default_options(app):
    return {'get_enabled' : False}