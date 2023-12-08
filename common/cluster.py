import pulumi
import pulumi_digitalocean as digitalocean

from common.networking import vpc
from common.project import do_region, project, stack

# Setup Vars
config = pulumi.Config('cluster')
size = config.get('node_size') or 's-1vcpu-2gb'
node_count = config.get_int('node_count') or 1
volume_size = config.get_int('volume_size') or 10

# Setup Cluster
cluster = digitalocean.KubernetesCluster(
    'k8s-cluster',
    name=f'{stack}-cluster',
    region=do_region,
    version='1.28.2-do.0',
    auto_upgrade=True,
    vpc_uuid=vpc.id,
    node_pool=digitalocean.KubernetesClusterNodePoolArgs(
        name=f'{stack}-node-pool',
        size=size,
        node_count=node_count,
    ),
    opts=pulumi.ResourceOptions(parent=project),
)

cluster_project_attachment = digitalocean.ProjectResources(
    'k8s-cluster-project-attachment',
    project=project.id,
    resources=[cluster.cluster_urn],
    opts=pulumi.ResourceOptions(parent=cluster),
)

volume = digitalocean.Volume(
    'k8s-cluster-volume',
    name=f'{stack}-common',
    size=volume_size,
    region=do_region,
    opts=pulumi.ResourceOptions(parent=cluster),
)

# Setup Outputs
pulumi.export('Kubernetes Cluster Endpoint', cluster.endpoint)
pulumi.export('Block Storage Volume Name', volume.name)
pulumi.export('Block Storage Volume Size', volume.size)
