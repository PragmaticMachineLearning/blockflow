
# class Config:
#     def __init__(self):
#         self.boundary_name = None

#     @property
#     def set_boundary_name(self, name):
#         print(f"Setting boundary name {name}")
#         self.boundary_name = name
    
                
#     def get_boundary_name(self):
#         print(f"Getting boundary name {self.boundary}")
#         self.boundary_name

CONFIG = {}


def set_boundary_name(name):
    global CONFIG
    CONFIG['boundary_name'] = name
    
def get_boundary_name():
    return CONFIG.get('boundary_name', None)