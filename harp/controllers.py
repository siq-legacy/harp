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
        'default_client_timeout', 'default_server_timeout', 'include_globals',
        'include_defaults']

    def acquire(self, subject):
        try:
            query = self.schema.session.query(self.model)
            return query.filter(Configuration.name==subject).one()
        except NoResultFound:
            return None

    def update(self, request, response, subject, data):
        commit = data.pop('commit', False)
        super(ConfigurationController, self).update(request, response, subject, data)
        
        if commit:
            subject.commit()

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
        'http_log', 'log_global']

class FrontendController(ProxyController):
    resource = resources.Frontend
    version = (1, 0)

    model = Frontend
    schema = SchemaDependency('harp')
    mapping = ['name', 'mode', 'connect_timeout', 'client_timeout', 'server_timeout',
        'forwardfor', 'forwardfor_header', 'http_close', 'http_server_close',
        'http_log', 'log_global', 'bind', 'default_backend']

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

class ACLController(ModelController):
    resource = resources.ACL
    version = (1, 0)

    model = ACL
    schema = SchemaDependency('harp')

    def acquire(self, subject):
        bundle = {'id': subject}
        try:
            bundle['conf_name'], bundle['proxy_name'], bundle['name'] = subject.split(':')
        except Exception:
            return None

        try:
            bundle['instances'] = list(self.schema.session.query(self.model)
                .join(Proxy, Configuration)
                .filter(Configuration.name==bundle['conf_name'])
                .filter(Proxy.name==bundle['proxy_name'])
                .filter(self.model.name==bundle['name']))
            return bundle
        except NoResultFound:
            return None

    def create(self, request, response, subject, data):
        conf_name, proxy_name, acl_name = data['id'].split(':')
        proxy = self._get_proxy(conf_name, proxy_name)

        session = self.schema.session
        for acl in data['acls']:
            instance = ACL(proxy_id=proxy.id, name=acl_name, acl=acl)
            session.add(instance)

        session.commit()
        response({'id': data['id']})

    def delete(self, request, response, subject, data):
        session = self.schema.session
        for instance in subject['instances']:
            session.delete(instance)

        session.commit()
        response({'id': subject['id']})

    def get(self, request, response, subject, data):
        acls = []
        for instance in subject['instances']:
            acls.append(instance.acl)

        response({
            'id': subject['id'],
            'name': subject['name'],
            'acls': acls})

    def update(self, request, response, subject, data):
        if not data:
            return response({'id': subject['id']})

        existing = {}
        for instance in subject['instances']:
            existing[instance.acl] = instance

        session = self.schema.session
        proxy = self._get_proxy(subject['conf_name'], subject['proxy_name'])

        for acl in data['acls']:
            if acl not in existing:
                session.add(ACL(proxy_id=proxy.id, name=subject['name'], acl=acl))
            else:
                del existing[acl]

        for instance in existing.itervalues():
            session.delete(instance)

        session.commit()
        response({'id': subject['id']})

    def _get_proxy(self, conf_name, proxy_name):
        return self.schema.session.query(Proxy).join(Configuration).filter(
            Configuration.name==conf_name, Proxy.name==proxy_name).one()

class RuleController(ElementController):
    resource = resources.Rule
    version = (1, 0)

    model = Rule
    schema = SchemaDependency('harp')
    mapping = 'name rule content'

class ServerController(ElementController):
    resource = resources.Server
    version = (1, 0)

    model = Server
    schema = SchemaDependency('harp')
    mapping = ['name', 'address', 'addr', 'backup', 'check', 'cookie', 'disabled',
        'error_limit', 'fall', 'inter', 'fastinter', 'downinter', 'maxconn', 'maxqueue',
        'minconn', 'observe', 'on_error', 'port', 'redir', 'rise', 'slowstart', 'track',
        'weight']
