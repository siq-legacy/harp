from mesh.standard import Bundle, mount
from scheme import Text
from spire.core import Component, Configuration
from spire.mesh import MeshServer

import harp.models
from harp import resources

API = Bundle('harp',
    mount(resources.ACL, 'harp.controllers.ACLController'),
    mount(resources.Backend, 'harp.controllers.BackendController'),
    mount(resources.Configuration, 'harp.controllers.ConfigurationController'),
    mount(resources.Frontend, 'harp.controllers.FrontendController'),
    mount(resources.Rule, 'harp.controllers.RuleController'),
    mount(resources.Server, 'harp.controllers.ServerController'))

class APIServer(MeshServer):
    pass

class Harp(Component):
    api = APIServer.deploy(
        bundles=[API],
        path='/')
