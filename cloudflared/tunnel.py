import pulumi
import pulumi_cloudflare as cloudflare
import pulumi_random as random

from common.cluster import cluster
from pretix.pretix import service as pretix_service
from pretix.pretix_config import host as pretix_host

# Setup Vars
config = pulumi.Config('cf')
stack = pulumi.get_stack()
account_id = config.require('accountID')
version_tag = config.get('versionTag') or '2023.10.0'

# Setup Tunnel
secret = random.RandomId(
    'cloudflare-tunnel-secret',
    byte_length=64,
    opts=pulumi.ResourceOptions(parent=cluster),
)

tunnel = cloudflare.Tunnel(
    'cloudflare-tunnel',
    name=pulumi.Output.all(cluster.region, cluster.name).apply(
        lambda args: f'{args[0]}-{args[1]}'
    ),
    account_id=account_id,
    secret=secret.b64_std,
    config_src='cloudflare',
    opts=pulumi.ResourceOptions(parent=cluster),
)

config = cloudflare.TunnelConfig(
    'cloudflare-tunnel-config',
    account_id=account_id,
    tunnel_id=tunnel.id,
    config=cloudflare.TunnelConfigConfigArgs(
        ingress_rules=[
            cloudflare.TunnelConfigConfigIngressRuleArgs(
                hostname=pretix_host,
                service=pulumi.Output.all(
                    pretix_service.metadata['name'],
                    pretix_service.metadata['namespace'],
                    pretix_service.spec.ports[0].port,
                ).apply(
                    lambda args: f'http://{args[0]}.{args[1]}.svc.cluster.local:{args[2]}'
                ),
            ),
            cloudflare.TunnelConfigConfigIngressRuleArgs(
                service='http_status:404',
            ),
        ],
        origin_request=cloudflare.TunnelConfigConfigOriginRequestArgs(
            no_happy_eyeballs=True,
        ),
    ),
    opts=pulumi.ResourceOptions(parent=tunnel),
)

# Setup Records
zone = cloudflare.get_zone(name='etcollective.org', account_id=account_id)

records = [pretix_host]
for record in records:
    dns_record = cloudflare.Record(
        f'{record}-record',
        name=record,
        zone_id=zone.zone_id,
        type='CNAME',
        value=tunnel.cname,
        proxied=True,
        comment='Managed by Pulumi',
        opts=pulumi.ResourceOptions(parent=tunnel),
    )

# Setup Outputs
pulumi.export('Cloudflare Tunnel CNAME', tunnel.cname)
pulumi.export('Cloudflare Tunnel Name', tunnel.name)
