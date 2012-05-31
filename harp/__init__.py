from mesh.standard import Bundle, mount
from spire.core import Component
from spire.mesh import MeshServer

import harp.models
from harp.resources import *

API = Bundle('harp',
    mount(ACL, 'harp.controllers.ACLController'),
    mount(Backend, 'harp.controllers.BackendController'),
    mount(Configuration, 'harp.controllers.ConfigurationController'),
    mount(Frontend, 'harp.controllers.FrontendController'),
    mount(Server, 'harp.controllers.ServerController'),
    mount(Target, 'harp.controllers.TargetController'))

class APIServer(MeshServer):
    pass

class Harp(Component):
    api = APIServer.deploy(
        bundles=[API],
        path='/')
