from xhrdrop import DropHandler

def get_handler_map(webroot):
    return [(webroot+'xhrdrop', DropHandler)]