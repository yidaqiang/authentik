"""authentik outposts app config"""

from prometheus_client import Gauge
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG

LOGGER = get_logger()

GAUGE_OUTPOSTS_CONNECTED = Gauge(
    "authentik_outposts_connected",
    "Currently connected outposts",
    ["tenant", "outpost", "uid", "expected"],
)
GAUGE_OUTPOSTS_LAST_UPDATE = Gauge(
    "authentik_outposts_last_update",
    "Last update from any outpost",
    ["tenant", "outpost", "uid", "version"],
)
MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"
MANAGED_OUTPOST_NAME = "authentik Embedded Outpost"


class AuthentikOutpostConfig(ManagedAppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"
    default = True

    def reconcile_global_load_outposts_signals(self):
        """Load outposts signals"""
        self.import_module("authentik.outposts.signals")

    def reconcile_tenant_embedded_outpost(self):
        """Ensure embedded outpost"""
        from authentik.outposts.models import (
            DockerServiceConnection,
            KubernetesServiceConnection,
            Outpost,
            OutpostType,
        )

        if not CONFIG.get_bool("outposts.disable_embedded_outpost", False):
            if outpost := Outpost.objects.filter(name=MANAGED_OUTPOST_NAME, managed="").first():
                outpost.managed = MANAGED_OUTPOST
                outpost.save()
                return
            outpost, updated = Outpost.objects.update_or_create(
                defaults={
                    "type": OutpostType.PROXY,
                    "name": MANAGED_OUTPOST_NAME,
                },
                managed=MANAGED_OUTPOST,
            )
            if updated:
                if KubernetesServiceConnection.objects.exists():
                    outpost.service_connection = KubernetesServiceConnection.objects.first()
                elif DockerServiceConnection.objects.exists():
                    outpost.service_connection = DockerServiceConnection.objects.first()
                outpost.save()
        else:
            Outpost.objects.filter(managed=MANAGED_OUTPOST).delete()
