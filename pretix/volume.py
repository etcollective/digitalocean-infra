import pulumi
import pulumi_digitalocean as digitalocean
import pulumi_kubernetes as k8s

from common.cluster import config
from common.project import do_region, stack
from pretix.namespace import ns

# Setup Vars
config = pulumi.Config('pretix')
volume_size = config.get_int('volume_size') or 10

# Setup Volume
volume = digitalocean.Volume(
    f'{stack}-pretix-volume',
    name=f'{stack}-pretix',
    size=volume_size,
    region=do_region,
    opts=pulumi.ResourceOptions(parent=ns, ignore_changes=['tags']),
)

pv = k8s.core.v1.PersistentVolume(
    f'{stack}-pretix-volume',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=volume.name,
        namespace=ns.metadata['name'],
        annotations={
            'pv.kubernetes.io/provisioned-by': 'dobs.csi.digitalocean.com',
        },
    ),
    spec=k8s.core.v1.PersistentVolumeSpecArgs(
        storage_class_name='do-block-storage',
        persistent_volume_reclaim_policy='Delete',
        capacity={
            'storage': volume.size.apply(lambda size: f'{size}Gi'),
        },
        access_modes=['ReadWriteOnce'],
        csi=k8s.core.v1.CSIPersistentVolumeSourceArgs(
            driver='dobs.csi.digitalocean.com',
            volume_handle=volume.id,
            volume_attributes={
                'com.digitalocean.csi/noformat': 'true',
            },
        ),
    ),
    opts=pulumi.ResourceOptions(parent=volume),
)

pvc = k8s.core.v1.PersistentVolumeClaim(
    f'{stack}-pvc',
    kind='PersistentVolumeClaim',
    api_version='v1',
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f'{stack}-pvc',
        namespace=ns.metadata['name'],
    ),
    spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
        volume_name=pv.metadata.name,
        access_modes=['ReadWriteOnce'],
        resources=k8s.core.v1.ResourceRequirementsArgs(
            requests={
                'storage': volume.size.apply(lambda size: f'{size}Gi'),
            },
        ),
    ),
    opts=pulumi.ResourceOptions(
        parent=pv, delete_before_replace=True, replace_on_changes=['metadata']
    ),
)

pulumi.export('Pretix Volume Name', volume.name)
pulumi.export('Pretix Volume Size', volume.size)
