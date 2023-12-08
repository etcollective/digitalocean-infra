"""
Deploy project resources, to be shared by all stacks.
"""

import pulumi
import pulumi_digitalocean as digitalocean

# Setup Vars
config = pulumi.Config('common')
stack = pulumi.get_stack()
do_region = config.require('region')

# Setup Project
project = digitalocean.Project(
    'project',
    name=stack,
    description=f'{stack} resources',
    environment=stack,
)

# Setup Outputs
pulumi.export('Project', project.name)
