import pulumi
import pulumi_kubernetes as k8s

from pretix.namespace import ns
from pretix.pretix_config import config_secret
from pretix.volume import pvc

# Setup Vars
config = pulumi.Config('pretix')
stack = pulumi.get_stack()
pretix_version = config.require('version_tag')
labels = {
    'app': 'pretix',
    'service': 'pretix',
    'env': stack,
}

deployment = k8s.apps.v1.Deployment(
    'pretix-deployment',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name='pretix-deployment',
        namespace=ns.metadata['name'],
        labels=labels,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={
                'app': 'pretix',
            },
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={
                    'app': 'pretix',
                },
            ),
            spec=k8s.core.v1.PodSpecArgs(
                init_containers=[
                    k8s.core.v1.ContainerArgs(
                        name='db-migrate',
                        image=f'pretix/standalone:{pretix_version}',
                        command=[
                            '/bin/sh',
                            '-c',
                            'pretix migrate',
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name='pretix-config',
                                mount_path='/etc/pretix/pretix.cfg',
                                sub_path='pretix.cfg',
                                read_only=True,
                            ),
                        ],
                    ),
                    k8s.core.v1.ContainerArgs(
                        name='take-data-dir-ownership',
                        image='alpine',
                        command=[
                            '/bin/sh',
                            '-c',
                            'chown -R 15371:15371 /data',
                            'chmod -R 700 /data',
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name='pretix',
                                mount_path='/data',
                                sub_path='pretix',
                            )
                        ],
                    ),
                ],
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name='pretix',
                        image=f'pretix/standalone:{pretix_version}',
                        env=[
                            k8s.core.v1.EnvVarArgs(
                                name='AUTOMIGRATE',
                                value='skip',
                            )
                        ],
                        ports=[
                            k8s.core.v1.ContainerPortArgs(
                                container_port=80,
                            )
                        ],
                        volume_mounts=[
                            k8s.core.v1.VolumeMountArgs(
                                name='pretix',
                                mount_path='/data',
                                sub_path='pretix',
                            ),
                            k8s.core.v1.VolumeMountArgs(
                                name='pretix-config',
                                mount_path='/etc/pretix/pretix.cfg',
                                sub_path='pretix.cfg',
                            ),
                        ],
                    )
                ],
                volumes=[
                    k8s.core.v1.VolumeArgs(
                        name='pretix',
                        persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
                            claim_name=pvc.metadata['name'],
                        ),
                    ),
                    k8s.core.v1.VolumeArgs(
                        name='pretix-config',
                        secret=k8s.core.v1.SecretVolumeSourceArgs(
                            secret_name=config_secret.metadata['name'],
                        ),
                    ),
                ],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(parent=ns),
)

service = k8s.core.v1.Service(
    'pretix-service',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name='pretix-service',
        namespace=ns.metadata['name'],
        labels=labels,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        selector={
            'app': 'pretix',
        },
        ports=[
            k8s.core.v1.ServicePortArgs(
                protocol='TCP',
                port=80,
                target_port=80,
            )
        ],
    ),
    opts=pulumi.ResourceOptions(parent=deployment),
)

# ingress = k8s.networking.v1.Ingress(
#     'pretix-ingress',
#     metadata=k8s.meta.v1.ObjectMetaArgs(
#         name='pretix-ingress',
#         namespace=ns.metadata['name'],
#         labels=labels,
#     ),
#     spec=k8s.networking.v1.IngressSpecArgs(
#         rules=[
#             k8s.networking.v1.IngressRuleArgs(
#                 host=host,
#                 http=k8s.networking.v1.HTTPIngressRuleValueArgs(
#                     paths=[
#                         k8s.networking.v1.HTTPIngressPathArgs(
#                             path='/',
#                             path_type='Prefix',
#                             backend=k8s.networking.v1.IngressBackendArgs(
#                                 service=k8s.networking.v1.IngressServiceBackendArgs(
#                                     name=service.metadata['name'],
#                                     port=k8s.networking.v1.ServiceBackendPortArgs(
#                                         number=service.spec.ports[0].port,
#                                     ),
#                                 ),
#                             ),
#                         )
#                     ],
#                 ),
#             )
#         ],
#     ),
#     opts=pulumi.ResourceOptions(parent=service, depends_on=[config_secret]),
# )
