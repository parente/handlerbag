'''
Server that can load Python modules defining handlers mapped to URLs. 

Copyright (c) 2010, 2011 Peter Parente. All Rights Reserved.
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
import logging
# handlerbag
import hbag
import login
import uuid

class HandlerBag(tornado.web.Application):
    def __init__(self, handlers=[], **kwargs):
        super(HandlerBag, self).__init__(handlers, **kwargs)
        # load the bag db
        self.db = shelve.open('hbdata')
        # import dynamic module
        self.modules = {}

        # store paths
        self.appPath = os.path.dirname(os.path.abspath(__file__))
        self.bagPath = os.path.dirname(hbag.__file__)
        self.dataPath = os.path.join(self.appPath, 'data')
        
        # update db to reflect available handlers
        self.refresh_handlers_in_db()
        
        # load all enabled handlers
        for name in self.db:
            if self.db[name]['enabled'] or name == 'admin':
                self.set_handler_status(name, True)
        
    def shutdown(self):
        # close the db cleanly
        self.db.close()
        
    def add_dynamic_handlers(self, host_pattern, host_handlers, options):
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
            handlers.append(spec)
            try:
                mtd = handler.register
            except AttributeError:
                return
            mtd(**options)
        
    def remove_dynamic_handler(self, host_pattern, url_pattern):
        handlers = None
        for regex, h in self.handlers:
            if regex.pattern == host_pattern:
                specs = h
                break
        if specs is None:
            raise ValueError('cannot remove handler for unknown host')
        i = 0
        if not url_pattern.endswith('$'):
            url_pattern += '$'
        while i < len(specs):
            spec = specs[i]
            if spec.regex.pattern == url_pattern:
                specs.pop(i)
                try:
                    mtd = spec.handler_class.unregister
                except AttributeError:
                    continue
                mtd()
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
            if not mod:
                try:
                    del self.db[name]
                except KeyError:
                    pass
                continue
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
            try:
                mod = __import__('hbag.'+name, fromlist=[name])
            except Exception:
                # bad module, log and bail
                logging.exception('failed to load %s', name)
                return
            self.modules[name] = mod
        else:
            # reload the module if loaded
            try:
                mod = reload(mod)
            except Exception:
                # bad module, log and bail
                logging.exception('failed to load %s', name)
                return
            self.modules[name] = mod
        return mod
    
    def set_handler_status(self, name, enable, opts=None):
        # not a known handler
        if not self.db.has_key(name): return
        info = self.db[name]

        # set the state in the db
        info = self.db[name]
        info['enabled'] = enable
        if opts is not None:
            info['options'] = opts
        self.db[name] = info

        # unregister existing handlers
        try:
            mod = self.modules[name]
        except KeyError:
            # nothing to do if never loaded and not enabling
            if not enable: return
        else:
            handlers = mod.get_handler_map(self, options.webroot, info['options'])
            for bag in handlers:
                try:
                    self.remove_dynamic_handler('.*$', bag[0])
                except ValueError:
                    pass
            # keep tracking module for later reload        

        if enable:
            opts = info['options']
            # register new handler
            mod = self.load_module(name)
            if mod:
                handlers = mod.get_handler_map(self, options.webroot, opts)
                self.add_dynamic_handlers('.*$', handlers, opts)
            else:
                try:
                    del self.db[name]
                except KeyError:
                    pass

if __name__ == '__main__':
    define('webroot', default='/', help='absolute root url of all handlers (default: /)')
    define('port', default=5000, type=int, help='server port (default: 5000)')
    define('debug', default=False, type=bool, help='enable debug autoreload (default: false)')
    define('cookie', default=uuid.uuid4().hex, help='secret key cookie signing (default: random)')
    tornado.options.parse_command_line()

    settings = {
        'login_url' : '/login',
        'auth_cookie' : 'handlerbag.user',
        'cookie_secret' : str(options.cookie),
        'debug' : options.debug
    }
    handlers = [
        ('/login/?', login.GoogleHandler)
    ]
    application = HandlerBag(handlers, **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    try:
        ioloop.start()
    finally:
        application.shutdown()
