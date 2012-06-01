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
    mount(resources.Server, 'harp.controllers.ServerController'),
    mount(resources.Target, 'harp.controllers.TargetController'))

class APIServer(MeshServer):
    pass

class Harp(Component):
    configuration = Configuration({
        'haproxy_path': Text(required=True, nonnull=True),
    })

    api = APIServer.deploy(
        bundles=[API],
        path='/')
