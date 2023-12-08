import pulumi
import pulumi_digitalocean as digitalocean

from common.project import do_region, project, stack

# Setup VPC
vpc = digitalocean.Vpc(
    'vpc',
    name=f'{stack}-vpc',
    region=do_region,
    opts=pulumi.ResourceOptions(parent=project),
)

# Setup Outputs
pulumi.export('VPC', vpc.name)
