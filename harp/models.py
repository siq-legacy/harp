from spire.schema import *

schema = Schema('harp')

class Configuration(Model):
    """An haproxy configuration."""

    class meta:
        schema = schema
        tablename = 'configuration'

    id = Identifier()
    name = Token(nullable=False, unique=True)
    filepath = Text(nullable=False, unique=True)
    pidfile = Text(nullable=False)
    chroot = Text()
    daemon = Boolean(default=True)
    group = Text()
    log_tag = Text()
    user = Text()
    default_mode = Enumeration('http tcp', default='http')
    default_connect_timeout = Text(default='5000ms')
    default_client_timeout = Text(default='50000ms')
    default_server_timeout = Text(default='50000ms')

    backends = relationship('Backend', backref='configuration')
    frontends = relationship('Frontend', backref='configuration')

    def render(self):
        globals = ['global']
        if self.chroot:
            globals.append('    chroot %s' % self.chroot)
        if self.daemon:
            globals.append('    daemon')
        if self.group:
            globals.append('    group %s' % self.group)
        if self.log_tag:
            globals.append('    log-tag %s' % self.log_tag)
        if self.pidfile:
            globals.append('    pidfile %s' % self.pidfile)
        if self.user:
            globals.append('    user %s' % self.user)

        defaults = ['defaults',
            '    mode %s' % self.default_mode,
            '    timeout connect %s' % self.default_connect_timeout,
            '    timeout client %s' % self.default_client_timeout,
            '    timeout server %s' % self.default_server_timeout,
        ]

        sections = ['\n'.join(globals), '\n'.join(defaults)]
        for frontend in self.frontends:
            sections.append(frontend.render())
        for backend in self.backends:
            sections.append(backend.render())

        return '\n\n'.join(sections)

class Proxy(Model):
    """A proxy."""

    class meta:
        polymorphic_on = 'type'
        schema = schema
        tablename = 'proxy'
        constraints = [UniqueConstraint('configuration_id', 'name')]

    id = Identifier()
    configuration_id = ForeignKey('configuration.id', nullable=False)
    type = Enumeration('frontend backend', nullable=False)
    name = Text(nullable=False)
    mode = Enumeration('http tcp')
    connect_timeout = Text()
    client_timeout = Text()
    server_timeout = Text()
    forwardfor = Boolean(default=False)
    forwardfor_header = Text()
    http_close = Boolean(default=False)
    http_server_close = Boolean(default=False)
    http_log = Boolean(default=False)

    acls = relationship('ACL', backref='proxy')

    TIMEOUTS = ('connect_timeout', 'client_timeout', 'server_timeout')

    def _render_common_options(self):
        options = []
        if self.mode is not None:
            options.append('    mode %s' % self.mode)

        for option in self.TIMEOUTS:
            value = getattr(self, option)
            if value is not None:
                options.append('    timeout %s %s' % (option[:-8].replace('_', '-'), value))

        if self.forwardfor:
            line = '    option forwardfor'
            if self.forwardfor_header:
                line += ' header %s' % self.forwardfor_header
            options.append(line)

        if self.http_log:
            options.append('    option httplog')
        if self.http_close:
            options.append('    option httpclose')
        if self.http_server_close:
            options.append('    option http-server-close')

        for acl in self.acls:
            options.append(acl.render())

        return options

class Backend(Proxy):
    """A backend proxy."""

    class meta:
        polymorphic_identity = 'backend'
        schema = schema
        tablename = 'backend'

    proxy_id = ForeignKey('proxy.id', nullable=False, primary_key=True)

    servers = relationship('Server', backref='proxy')

    def render(self):
        options = ['backend %s' % self.name]
        options.extend(self._render_common_options())

        for server in self.servers:
            options.append(server.render())

        return '\n'.join(options)

class Frontend(Proxy):
    """A frontend proxy."""

    class meta:
        polymorphic_identity = 'frontend'
        schema = schema
        tablename = 'frontend'

    proxy_id = ForeignKey('proxy.id', nullable=False, primary_key=True)
    bind = Text(nullable=False)
    default_backend = Text()

    targets = relationship('Target', backref='proxy', order_by='Target.rank')

    def render(self):
        options = ['frontend %s' % self.name, '    bind %s' % self.bind]
        options.extend(self._render_common_options())

        for target in self.targets:
            options.append(target.render())

        if self.default_backend:
            options.append('    default_backend %s' % self.default_backend)

        return '\n'.join(options)

class ACL(Model):
    """An ACL."""

    class meta:
        schema = schema
        tablename = 'acl'
        constraints = [UniqueConstraint('proxy_id', 'name')]

    id = Identifier()
    proxy_id = ForeignKey('proxy.id', nullable=False)
    name = Token(nullable=False)
    acl = Text(nullable=False)

    def render(self):
        return '    acl %s %s' % (self.name, self.acl)

class Server(Model):
    """A backend server."""

    class meta:
        schema = schema
        tablename = 'server'
        constraints = [UniqueConstraint('proxy_id', 'name')]

    id = Identifier()
    proxy_id = ForeignKey('proxy.id', nullable=False)
    name = Token(nullable=False)
    address = Text(nullable=False)
    addr = Text()
    backup = Boolean(default=False)
    check = Boolean(default=False)
    cookie = Text()
    disabled = Boolean(default=False)
    error_limit = Integer()
    fall = Integer()
    inter = Integer()
    fastinter= Integer()
    downinter = Integer()
    maxconn = Integer()
    maxqueue = Integer()
    minconn = Integer()
    observe = Text()
    on_error = Text()
    port = Integer()
    redir = Text()
    rise = Integer()
    slowstart = Integer()
    track = Text()
    weight = Integer()

    OPTIONS = ('addr', 'backup', 'check', 'cookie', 'disabled', 'error_limit', 'fall', 'inter',
        'fastinter', 'downinter', 'maxconn', 'maxqueue', 'minconn', 'observe', 'on_error',
        'port', 'redir', 'rise', 'slowstart', 'track', 'weight')

    def render(self):
        options = []
        for option in self.OPTIONS:
            value = getattr(self, option)
            if isinstance(value, bool):
                if value:
                    options.append(option.replace('_', '-'))
            elif value is not None:
                options.append('%s %s' % (option.replace('_', '-'), value))

        return '    server %s %s %s' % (self.name, self.address, ' '.join(options))

class Target(Model):
    """A frontend target."""

    class meta:
        schema = schema
        tablename = 'target'
        constraints = [UniqueConstraint('proxy_id', 'rank')]

    id = Identifier()
    proxy_id = ForeignKey('proxy.id', nullable=False)
    rank = Integer(nullable=False, minimum=1)
    backend = Text(nullable=False)
    operator = Enumeration('if unless', default='if')
    condition = Text(nullable=False)

    def render(self):
        return '    use_backend %s %s %s' % (self.backend, self.operator, self.condition)
