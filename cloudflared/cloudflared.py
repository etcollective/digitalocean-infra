import pulumi
import pulumi_kubernetes as k8s

from cloudflared.tunnel import stack, tunnel, version_tag
from common.cluster import cluster
from common.provider import provider

# Deploy Namespace
ns = k8s.core.v1.Namespace(
    'cloudflared-namespace',
    metadata={
        'name': 'cloudflared',
    },
    opts=pulumi.ResourceOptions(
        provider=provider, depends_on=[provider], parent=cluster
    ),
)

secret = k8s.core.v1.Secret(
    'cloudflared-secret',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name='cloudflared-token',
        namespace=ns.metadata.name,
    ),
    string_data={
        'TUNNEL_TOKEN': tunnel.tunnel_token,
    },
    opts=pulumi.ResourceOptions(parent=ns),
)

deployment = k8s.apps.v1.Deployment(
    'cloudflared-deployment',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name='cloudflared',
        namespace=ns.metadata.name,
        labels={
            'app': 'cloudflared',
            'env': stack,
        },
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={
                'app': 'cloudflared',
            },
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={
                    'app': 'cloudflared',
                },
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name='cloudflared',
                        image=f'cloudflare/cloudflared:{version_tag}',
                        command=[
                            'cloudflared',
                            'tunnel',
                            '--metrics',
                            '0.0.0.0:2000',
                            'run',
                        ],
                        liveness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path='/ready',
                                port=2000,
                            ),
                            failure_threshold=1,
                            initial_delay_seconds=10,
                            period_seconds=10,
                        ),
                        env=[
                            k8s.core.v1.EnvVarArgs(
                                name='NO_AUTOUPDATE',
                                value='true',
                            ),
                        ],
                        env_from=[
                            k8s.core.v1.EnvFromSourceArgs(
                                secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                    name=secret.metadata.name,
                                ),
                            )
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            limits={
                                'cpu': '500m',
                                'memory': '512Mi',
                            },
                            requests={
                                'cpu': '1m',
                                'memory': '10Mi',
                            },
                        ),
                        security_context=k8s.core.v1.SecurityContextArgs(
                            read_only_root_filesystem=True,
                        ),
                    ),
                ],
                termination_grace_period_seconds=30,
                dns_policy='ClusterFirst',
                automount_service_account_token=False,
            ),
        ),
        strategy=k8s.apps.v1.DeploymentStrategyArgs(
            type='RollingUpdate',
            rolling_update=k8s.apps.v1.RollingUpdateDeploymentArgs(
                max_unavailable='25%',
                max_surge='25%',
            ),
        ),
        revision_history_limit=1,
        progress_deadline_seconds=600,
    ),
    opts=pulumi.ResourceOptions(parent=ns, depends_on=[tunnel]),
)

# Setup Outputs
pulumi.export('Cloudflare Namespace', ns.metadata['name'])
pulumi.export('cloudflared Deployment', deployment.metadata['name'])
