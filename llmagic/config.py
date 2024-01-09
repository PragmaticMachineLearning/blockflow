CONFIG = {}


def set_boundary_name(name):
    global CONFIG
    CONFIG["boundary_name"] = name


def get_boundary_name():
    return CONFIG.get("boundary_name", None)
