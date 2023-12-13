import pulumi
import pulumi_kubernetes as k8s

from common.provider import provider

# Deploy Namespace
ns = k8s.core.v1.Namespace(
    'pretix-namespace',
    metadata={
        'name': 'pretix',
    },
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[provider]),
)

pulumi.export('namespace', ns.metadata['name'])
