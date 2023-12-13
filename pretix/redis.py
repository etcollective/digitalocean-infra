import pulumi
import pulumi_kubernetes as k8s

from pretix.namespace import ns
from pretix.volume import pvc

# Setup Vars
config = pulumi.Config('redis')
stack = pulumi.get_stack()
chart_version = config.get('version') or '18.4.0'

# Setup Redis
redis_chart = k8s.helm.v3.Chart(
    'redis-chart',
    k8s.helm.v3.ChartOpts(
        chart='redis',
        version=chart_version,
        fetch_opts=k8s.helm.v3.FetchOpts(
            repo='https://charts.bitnami.com/bitnami'
        ),
        namespace=ns.metadata['name'],
        values={
            'architecture': 'standalone',
            'auth': {
                'enabled': config.get_bool('authEnabled'),
            },
            'commonLabels': {
                'app': 'pretix',
                'component': 'redis',
                'env': stack,
            },
            'master': {
                'count': config.get('master_nodes'),
                'persistence': {
                    'enabled': True,
                    'existingClaim': pvc.metadata['name'],
                    'subPath': 'redis',
                },
            },
            'replica': {
                'count': config.get('replica_nodes') or '0',
            },
            'volumePermissions': {
                'enabled': True,
            },
        },
    ),
    opts=pulumi.ResourceOptions(parent=ns),
)

redis_service = (
    redis_chart.resources['v1/Service:pretix/redis-chart-master']
    .metadata['name']
    .apply(lambda redis: redis)
)

redis_port = (
    redis_chart.resources['v1/Service:pretix/redis-chart-master']
    .spec.ports[0]
    .port.apply(lambda port: port)
)

# Setup Outputs
pulumi.export(
    'Pretix Redis Service',
    redis_service,
)
pulumi.export(
    'Pretix Redis Port',
    redis_port,
)
