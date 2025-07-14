import json
from json import JSONEncoder

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
    
class User(object):
    def __init__(self, id,nombre,correo,permisos,pwo):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.permisos = permisos
        self.pwo = pwo

    def __str__(self):
        return "User(id='%s')" % self.id

    def toJSON(self):
        return json.dumps(self.__dict__)
class FullTemplate(object):
    def __init__(self, template,params):
        self.template = template
        self.params = params
        

    def __str__(self):
        return "User(id='%s')" % self.id

    def toJSON(self):
        return json.dumps(self.__dict__)
        