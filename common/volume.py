import pulumi
import pulumi_digitalocean as digitalocean

from common.cluster import cluster, config
from common.project import do_region, stack

# Setup Vars
volume_size = config.get_int('volume_size') or 10

# Setup Volume
volume = digitalocean.Volume(
    'k8s-cluster-volume',
    name=f'{stack}-common',
    size=volume_size,
    region=do_region,
    opts=pulumi.ResourceOptions(parent=cluster),
)

pulumi.export('Block Storage Volume Name', volume.name)
pulumi.export('Block Storage Volume Size', volume.size)
