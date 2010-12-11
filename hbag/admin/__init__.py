from admin import AdminHandler

def get_handler_map(app, webroot, **options):
    return [(webroot+'admin/?', AdminHandler)]

def get_default_options(app):
    return {}