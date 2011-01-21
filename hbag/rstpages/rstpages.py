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
import glob
import time

class PageWatcher(PatternMatchingEventHandler):
    def __init__(self, options={}, **kwargs):
        super(PageWatcher, self).__init__(**kwargs)
        self.options = options
    
    def _render(self, path):
        root, ext = os.path.splitext(path)
        opts = self.options.get('writer_opts')
        args = ['rst2html-pygments']
        if opts: args.extend(opts)
        args.extend([path, root + '.html'])
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
        w = PageWatcher(patterns=['*.rst'], options=options)
        # render existing documents
        for fn in glob.glob(os.path.join(path, '*.rst')):
            root, ext = os.path.splitext(fn)
            html = root+'.html'
            if not os.path.isfile(html):
                w._render(html)
        ob.schedule(w, path)
        ob.start()

    @classmethod
    def unregister(cls):
        cls.observer.stop()
        cls.observer.join()
        
    def initialize(self, writer_opts, **kwargs):
        super(RstPagesHandler, self).initialize(**kwargs)
    
    def get(self, fn, *args, **kwargs):
        if not fn:
            # generate index
            docs = [(os.path.basename(fn), time.ctime(os.stat(fn).st_mtime))
                for fn in glob.glob(os.path.join(self.root, '*.html'))]
            docs.sort()
            self.render('rstpages.html', docs=docs)
        else:
            super(RstPagesHandler, self).get(fn, *args, **kwargs)

def get_handler_map(app, webroot, options):
    return [(webroot+'rstpages/?(.*)', RstPagesHandler, options)]

def get_default_options(app):
    return {
        'path' : os.path.join(app.dataPath, 'rstpages'),
        'writer_opts' : [
            '--stylesheet-path='+os.path.join(app.bagPath, 'rstpages', 'lsr.css'),
            '--strip-comments',
            '--generator',
            '--field-name-limit=20',
            '--date',
            '--time'
        ]
    }