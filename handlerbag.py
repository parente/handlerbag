'''
Server that can load Python modules defining handlers mapped to URLs. 

:requires: Python 2.6, Tornado 1.0
:copyright: Peter Parente 2010
:license: BSD
'''
# tornado
import tornado.web
import tornado.httpserver
from tornado.options import define, options
# std lib
import glob
import os.path
import shelve
import sys
# handlerbag
import hbag

class HandlerBag(tornado.web.Application):
    def __init__(self, **kwargs):
        # always enabled debug for auto reload
        kwargs['debug'] = False
        # load the bag db
        self.db = shelve.open('hbdata')
        # import dynamic module
        self.modules = {}
        
        # always load the admin handler
        import hbag.admin as admin
        handlers = hbag.admin.get_handler_map(options.webroot)
        self.modules['admin'] = admin
        
        # store paths
        self.appPath = os.path.dirname(os.path.abspath(__file__))
        self.bagPath = os.path.dirname(hbag.__file__)

        # set the initial handlers and options
        super(HandlerBag, self).__init__(handlers, **kwargs)
        
    def shutdown(self):
        # close the db cleanly
        self.db.close()
        
    def add_dynamic_handlers(self, host, handlers, pos=0):
        handlers = None
        for regex, h in self.handlers:
            if regex.pattern == host_pattern:
                handlers = h
                break
        if handlers is None:
            raise ValueError('cannot extend handlers for unknown host')
        for spec in host_handlers:
            if type(spec) is type(()):
                assert len(spec) in (2, 3)
                pattern = spec[0]
                handler = spec[1]
                if len(spec) == 3:
                    kwargs = spec[2]
                else:
                    kwargs = {}
                spec = tornado.web.URLSpec(pattern, handler, kwargs)
            handlers.insert(pos, spec)
        
    def remove_dynamic_handler(self, host, url):
        handlers = None
        for regex, h in self.handlers:
            if regex.pattern == host_pattern:
                handlers = h
                break
        if handlers is None:
            raise ValueError('cannot remove handler for unknown host')
        i = 0
        if not url_pattern.endswith('$'):
            url_pattern += '$'
        while i < len(handlers):
            handler = handlers[i]
            if handler.regex.pattern == url_pattern:
                handlers.pop(i)
            else:
                i += 1
    
    def refresh_handlers_in_db(self):
        g = glob.glob(os.path.join(self.bagPath, '*'))
        avail = set((os.path.basename(d) for d in g if os.path.isdir(d)))
        known = set(self.db.keys())
        new = avail - known
        for name in new:
            self.db[name] = {'enabled' : False, 'options' : {}}
        old = known - avail
        for name in old:
            del self.db[name]
        return self.db
    
    def set_handler_status(self, name, enable):
        # not a known handler
        if not self.db.has_key(name): return
        info = self.db[name]
        # no change
        if info['enabled'] == enable: return

        # set the state in the db
        info = self.db[name]
        info['enabled'] = enable
        self.db[name] = info
        
        # check if module already loaded

if __name__ == '__main__':
    define('webroot', default='/', help='absolute root url of all handlers (default: /)')
    define('port', default=5000, type=int, help='drop server port (default: 5000)')
    tornado.options.parse_command_line()

    application = HandlerBag()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    try:
        ioloop.start()
    finally:
        application.shutdown()
