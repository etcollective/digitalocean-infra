# Setup Config File
import pulumi
import pulumi_kubernetes as k8s

import pretix.postgres as db
from pretix.namespace import ns
from pretix.redis import redis_port, redis_service

# Setup Vars
config = pulumi.Config('pretix')
stack = pulumi.get_stack()

host = config.require('host')
instance_name = config.require('instance_name')
url = f'https://{host}'
labels = {
    'app': 'pretix',
    'service': 'pretix',
    'env': stack,
}


smtp_host = config.require('smtp_host')
smtp_port = config.require_int('smtp_port')
smtp_from = config.require('smtp_from')

# Setup Secret
config_secret = k8s.core.v1.Secret(
    'pretix-config-secret',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name='pretix-config-secret',
        namespace=ns.metadata['name'],
        labels=labels,
    ),
    string_data={
        'pretix.cfg': pulumi.Output.all(
            db.db_password.result,
            redis_service,
            redis_port,
        ).apply(
            lambda args: f"""
    [pretix]
    instance_name={instance_name}
    url={url}
    currency=USD
    datadir=/data
    trust_x_forwarded_for=on
    trust_x_forwarded_proto=on

    [locale]
    timezone=America/Phoenix
    
    [database]
    backend=postgresql
    name={db.db_name}
    user={db.username}
    password={args[0]}
    host=postgres-chart-postgresql
    port=5432

    [mail]
    from={smtp_from}
    host={smtp_host}
    tls=on
    port={smtp_port}

    [redis]
    location=redis://{args[1]}:{args[2]}/0

    [celery]
    backend=redis://{args[1]}:{args[2]}/1
    broker=redis://{args[1]}:{args[2]}/2
"""
        ),
    },
    opts=pulumi.ResourceOptions(parent=ns),
)
