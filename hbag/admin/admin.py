'''Simple admin panel for handler config.'''
# tornado
import tornado.web
# std lib
import json

class AdminHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        # force update of handler list
        db = self.application.refresh_handlers_in_db()
        # show all handlers but ourselves
        items = (item for item in db.iteritems() if item[0] != 'admin')
        self.render('admin.html', items=items)
        
    def post(self, *args, **kwargs):
        obj = json.loads(self.request.body)
        for name, enabled in obj.iteritems():
            self.application.set_handler_status(name, enabled)