'''Downloads a file given a URL to a local directory on the server.'''
# tornado
import tornado.web
from tornado.simple_httpclient import SimpleAsyncHTTPClient
# std lib
import json
import os.path
import urlparse
import datetime
# handlerbag
import users

class URLFetchHandler(tornado.web.RequestHandler):
    def initialize(self, **options):
        self.options = options

    def get_current_user(self):
        return self.get_secure_cookie(self.settings['auth_cookie'])
    
    @tornado.web.authenticated
    @users.requireRole('admin')
    def get(self):
        self.render('urlfetch.html', result='')

    @tornado.web.authenticated
    @users.requireRole('admin')
    @tornado.web.asynchronous
    def post(self):
        url = self.get_argument('url')
        http = SimpleAsyncHTTPClient()
        http.fetch(url, callback=self.on_fetch_complete)
    
    def on_fetch_complete(self, resp):
        if resp.error is None:
            result = 'Downloaded %s' % resp.effective_url
            fn = os.path.basename(resp.effective_url)
            if not fn:
                # make up a filename based on the datetime
                fn = datetime.datetime.now().isoformat()
            fn = os.path.join(self.options['path'], fn)
            with file(fn, 'wb') as out:
                while 1:
                    bytes = resp.buffer.read(int(self.options['buffer_size']))
                    if not bytes: break
                    out.write(bytes)
        else:
            result = str(resp.error)            
        self.render('urlfetch.html', result=result)

def get_handler_map(app, webroot, options):
    return [(webroot+'urlfetch/?', URLFetchHandler, options)]

def get_default_options(app):
    return {
        'buffer_size' : 4096,
        'path' : os.path.join(app.dataPath, 'urlfetch')
    }