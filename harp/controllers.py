from spire.mesh import ModelController
from spire.schema import NoResultFound, SchemaDependency

from harp.models import *
from harp import resources

class ConfigurationController(ModelController):
    resource = resources.Configuration
    version = (1, 0)

    model = Configuration
    schema = SchemaDependency('harp')
    mapping = [('id', 'name'), 'filepath', 'pidfile', 'chroot', 'daemon', 'group',
        'log_tag', 'user', 'default_mode', 'default_connect_timeout',
        'default_client_timeout', 'default_server_timeout']

    def acquire(self, subject):
        try:
            query = self.schema.session.query(self.model)
            return query.filter(Configuration.name==subject).one()
        except NoResultFound:
            return None

class ProxyController(ModelController):
    def acquire(self, subject):
        try:
            conf_name, proxy_name = subject.split(':')
        except Exception:
            return None

        try:
            return self.schema.session.query(self.model).join(Configuration).filter(
                Configuration.name==conf_name, self.model.name==proxy_name).one()
        except NoResultFound:
            return None

    def _annotate_model(self, request, model, data):
        conf_name, model.name = data['id'].split(':')
        model.configuration = self.schema.session.query(Configuration).filter(
            Configuration.name==conf_name).one()

    def _annotate_resource(self, request, model, resource, data):
        resource['id'] = self._get_model_value(model, 'id')

    def _get_model_value(self, model, name):
        if name == 'id':
            return '%s:%s' % (model.configuration.name, model.name)
        else:
            return super(ProxyController, self)._get_model_value(model, name)

class BackendController(ProxyController):
    resource = resources.Backend
    version = (1, 0)

    model = Backend
    schema = SchemaDependency('harp')
    mapping = ['name', 'mode', 'connect_timeout', 'client_timeout', 'server_timeout',
        'forwardfor', 'forwardfor_header', 'http_close', 'http_server_close',
        'http_log']

class FrontendController(ProxyController):
    resource = resources.Frontend
    version = (1, 0)

    model = Frontend
    schema = SchemaDependency('harp')
    mapping = ['name', 'mode', 'connect_timeout', 'client_timeout', 'server_timeout',
        'forwardfor', 'forwardfor_header', 'http_close', 'http_server_close',
        'http_log', 'bind', 'default_backend']

class ElementController(ModelController):
    def acquire(self, subject):
        try:
            conf_name, proxy_name, element_name = subject.split(':')
        except Exception:
            return None

        try:
            return (self.schema.session.query(self.model)
                .join(Proxy, Configuration)
                .filter(Configuration.name==conf_name)
                .filter(Proxy.name==proxy_name)
                .filter(self.model.name==element_name)).one()
        except NoResultFound:
            return None

    def _annotate_model(self, request, model, data):
        conf_name, proxy_name, model.name = data['id'].split(':')
        model.proxy = self.schema.session.query(Proxy).join(Configuration).filter(
            Configuration.name==conf_name, Proxy.name==proxy_name).one()

    def _annotate_resource(self, request, model, resource, data):
        resource['id'] = self._get_model_value(model, 'id')

    def _get_model_value(self, model, name):
        if name == 'id':
            proxy = model.proxy
            return '%s:%s:%s' % (proxy.configuration.name, proxy.name, model.name)
        else:
            return super(ElementController, self)._get_model_value(model, name)

class ACLController(ElementController):
    resource = resources.ACL
    version = (1, 0)

    model = ACL
    schema = SchemaDependency('harp')
    mapping = 'name acl'

class ServerController(ElementController):
    resource = resources.Server
    version = (1, 0)

    model = Server
    schema = SchemaDependency('harp')
    mapping = ['name', 'address', 'addr', 'backup', 'check', 'cookie', 'disabled',
        'error_limit', 'fall', 'inter', 'fastinter', 'downinter', 'maxconn', 'maxqueue',
        'minconn', 'observe', 'on_error', 'port', 'redir', 'rise', 'slowstart', 'track',
        'weight']

class TargetController(ModelController):
    resource = resources.Target
    version = (1, 0)

    model = Target
    schema = SchemaDependency('harp')
    mapping = 'rank backend operator condition'

    def acquire(self, subject):
        try:
            conf_name, proxy_name, rank = subject.split(':')
        except Exception:
            return None

        rank = int(rank)
        try:
            return (self.schema.session.query(self.model)
                .join(Proxy, Configuration)
                .filter(Configuration.name==conf_name)
                .filter(Proxy.name==proxy_name)
                .filter(self.model.rank==rank)).one()
        except NoResultFound:
            return None

    def _annotate_model(self, request, model, data):
        conf_name, proxy_name, rank = data['id'].split(':')
        model.rank = int(rank)
        model.proxy = (self.schema.session.query(Proxy)
            .join(Configuration)
            .filter(Configuration.name==conf_name)
            .filter(Proxy.name==proxy_name)).one()

    def _annotate_resource(self, request, model, resource, data):
        resource['id'] = self._get_model_value(model, 'id')

    def _get_model_value(self, model, name):
        if name == 'id':
            proxy = model.proxy
            return '%s:%s:%s' % (proxy.configuration.name, proxy.name, model.rank)
        else:
            return super(TargetController, self)._get_model_value(model, name)
