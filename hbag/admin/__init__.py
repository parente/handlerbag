from admin import AdminHandler

def get_handler_map(webroot):
    return [(webroot+'admin/?', AdminHandler)]

def get_handler_opts():
    return {}