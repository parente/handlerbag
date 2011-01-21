'''
Allowed users and their roles.

Copyright (c) 2010, 2011 Peter Parente. All Rights Reserved.
'''
# tornado
import tornado.web

allowed = {
    'parente@gmail.com' : 'admin'
}

def requireRole(role='admin'):
    def wrap(method):        
        def wrapped_m(self, *args, **kwargs):
            if allowed.get(self.current_user, '') != role:
                raise tornado.web.HTTPError(403)
            return method(self, *args, **kwargs)
        return wrapped_m
    return wrap