# tornado
import tornado.web
import tornado.auth
# handlerbag
import users

class GoogleHandler(tornado.web.RequestHandler, tornado.auth.GoogleMixin):
    NEXT_COOKIE='handlerbag.next'
    def get_current_user(self):
        return self.get_secure_cookie(self.settings['auth_cookie'])
    
    @tornado.web.asynchronous
    def get(self):        
        if self.get_argument('openid.mode', None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
        else:
            # save next into a temp cookie
            next = self.request.arguments.get('next', ['/'])[0]
            self.set_secure_cookie(self.NEXT_COOKIE, next)
            self.authenticate_redirect(ax_attrs=['email'])

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, 'Google auth failed')
        self.set_secure_cookie(self.settings['auth_cookie'], user['email'])
        next = self.get_secure_cookie(self.NEXT_COOKIE)
        self.clear_cookie(self.NEXT_COOKIE)
        self.redirect(next)