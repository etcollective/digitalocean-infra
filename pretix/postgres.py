import pulumi
import pulumi_kubernetes as k8s
import pulumi_random as random

from pretix.namespace import ns
from pretix.volume import pvc

# Setup Vars
config = pulumi.Config('db')
stack = pulumi.get_stack()
username = config.get('username') or 'pretixuser'
db_name = config.get('name') or 'pretix'
chart_version = config.get('chart_version') or '13.2.24'

db_password = random.RandomPassword(
    'db-password',
    length=16,
    special=True,
    opts=pulumi.ResourceOptions(parent=ns),
)

postgres_chart = k8s.helm.v3.Chart(
    'postgres-chart',
    k8s.helm.v3.ChartOpts(
        chart='postgresql',
        version=chart_version,
        namespace=ns.metadata['name'],
        fetch_opts=k8s.helm.v3.FetchOpts(
            repo='https://charts.bitnami.com/bitnami'
        ),
        values={
            'commonLabels': {
                'app': 'pretix',
                'component': 'db',
                'env': stack,
            },
            'global': {
                'postgresql': {
                    'auth': {
                        'username': username,
                        'password': db_password.result,
                        'database': db_name,
                    },
                },
            },
            'primary': {
                'persistence': {
                    'enabled': 'true',
                    'existingClaim': pvc.metadata['name'],
                    'subPath': 'postgres',
                },
            },
            'volumePermissions': {
                'enabled': True,
            },
            'metrics': {
                'enabled': True,
            },
        },
    ),
    opts=pulumi.ResourceOptions(parent=ns),
)
