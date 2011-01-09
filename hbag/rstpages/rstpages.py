'''Builds reStructuredText files into HTML as they change.'''
# tornado
import tornado.web
# watchdog
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler
# std lib
import os.path
import datetime
import urlparse
import subprocess

class PageWatcher(PatternMatchingEventHandler):
    def _render(self, path):
        root, ext = os.path.splitext(path)
        args = ['rst2html-pygments', path, root + '.html']
        subprocess.call(args)

    def _remove(self, path):
        # rm html for old file
        root, ext = os.path.splitext(path)
        try:
            os.remove(root + '.html')
        except OSError:
            pass        
    
    def on_created(self, event):
        self._render(event.src_path)
        
    def on_deleted(self, event):
        self._remove(event.src_path)
    
    def on_modified(self, event):
        self._render(event.src_path)
    
    def on_moved(self, event):
        self._remove(event.src_path)
        self._render(event.dest_path)        

class RstPagesHandler(tornado.web.StaticFileHandler):
    @classmethod
    def register(cls, path='.', **options):
        ob = cls.observer = PollingObserver()
        w = PageWatcher(patterns=['*.rst'])
        # crash if unicode
        path = path.encode('utf-8')
        ob.schedule(w, path)
        ob.start()
    
    @classmethod
    def unregister(cls):
        cls.observer.stop()
        cls.observer.join()
    
    def get(self, fn, *args, **kwargs):
        print fn, args, kwargs
        if not fn:
            # generate index
            print 'here'
            pass
        else:
            super(RstPagesHandler, self).get(fn, *args, **kwargs)

def get_handler_map(app, webroot, options):
    return [(webroot+'rstpages/?(.*)', RstPagesHandler, options)]

def get_default_options(app):
    return {
        'path' : os.path.join(app.dataPath, 'rstpages')
    }