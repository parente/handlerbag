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
import re
# handlerbag
import hbag

class HandlerBag(tornado.web.Application):
    def __init__(self, **kwargs):
        super(HandlerBag, self).__init__([], **kwargs)
        # load the bag db
        self.db = shelve.open('hbdata')
        # import dynamic module
        self.modules = {}

        # store paths
        self.appPath = os.path.dirname(os.path.abspath(__file__))
        self.bagPath = os.path.dirname(hbag.__file__)
        
        # update db to reflect available handlers
        self.refresh_handlers_in_db()
        
        # load all enabled handlers
        for name in self.db:
            if self.db[name]['enabled'] or name == 'admin':
                self.set_handler_status(name, True)
        
    def shutdown(self):
        # close the db cleanly
        self.db.close()
        
    def add_dynamic_handlers(self, host_pattern, host_handlers, pos=0):
        handlers = None
        for regex, h in self.handlers:
            if regex.pattern == host_pattern:
                handlers = h
                break
        if handlers is None:
            handlers = []
            self.handlers.append((re.compile(host_pattern), handlers))
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
        
    def remove_dynamic_handler(self, host_pattern, url_pattern):
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
        # grab packages
        g = glob.glob(os.path.join(self.bagPath, '*'))
        avail = set((os.path.basename(d) for d in g if os.path.isdir(d)))
        # grab modules
        g = glob.glob(os.path.join(self.bagPath, '*.py'))
        avail.update((os.path.basename(d).split('.')[0] 
            for d in g if not d.endswith('__init__.py')))
        
        known = set(self.db.keys())
        for name in avail:
            info = self.db.get(name, {})
            mod = self.load_module(name)
            opts = mod.get_default_options(self)
            try:
                desc = mod.__doc__.split('\n')[0]
            except (AttributeError, IndexError):
                desc = ''
            enabled = info.get('enabled', False)

            if (info is None or 
                desc != info.get('description') or 
                set(opts) ^ set(info.get('options', []))):
                # put new metadata into the db
                self.db[name] = {
                    'enabled' : enabled,
                    'description' : desc,
                    'options' : opts
                }

        old = known - avail
        for name in old:
            del self.db[name]
        return self.db
        
    def load_module(self, name):
        # check if module already loaded
        try:
            mod = self.modules[name]
        except KeyError:
            # load the module for the first time
            mod = __import__('hbag.'+name, fromlist=[name])
            self.modules[name] = mod
        else:
            # reload the module if loaded
            mod = reload(mod)
            self.modules[name] = mod
        return mod
    
    def set_handler_status(self, name, enable):
        # not a known handler
        if not self.db.has_key(name): return
        info = self.db[name]

        # set the state in the db
        info = self.db[name]
        info['enabled'] = enable
        self.db[name] = info
        
        # unregister existing handlers
        try:
            mod = self.modules[name]
        except KeyError:
            # nothing to do if never loaded and not enabling
            if not enable: return
        else:
            handlers = mod.get_handler_map(self, options.webroot, **info['options'])
            for bag in handlers:
                try:
                    self.remove_dynamic_handler('.*$', bag[0])
                except ValueError:
                    pass
            # keep tracking module for later reload        

        if enable:
            # register new handler
            mod = self.load_module(name)
            handlers = mod.get_handler_map(self, options.webroot, **info['options'])
            self.add_dynamic_handlers('.*$', handlers)

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
