import pulumi
import pulumi_kubernetes as k8s

from common.cluster import cluster

provider = k8s.Provider(
    'k8s-provider',
    kubeconfig=cluster.kube_configs[0].raw_config,
    opts=pulumi.ResourceOptions(parent=cluster, depends_on=[cluster]),
)
