
import Domoticz
try:
    from Domoticz import Devices
except ImportError:
    pass
import logging

LOGGER = logging.getLogger(__name__)

from Modules.domo_create import domoCreateDevice
from Modules.domo_maj import domoMajDevice


class MainListener:
    """
    Contains callbacks that zigpy will call whenever something happens.
    Look for `listener_event` in the Zigpy source or just look at the logged warnings.
    """
    def __init__(self, application, Devices):
        Domoticz.Log("MainListener init App: %s Devices: %s" %(application, Devices))
        self.application = application
        self.domoticzDevices = Devices

    def device_joined(self, device):
        Domoticz.Log(f"Device joined: {device}")
        Domoticz.Log(" - NwkId: %s" %device.nwk)
        Domoticz.Log(" - IEEE: %s" %device._ieee)


    def device_announce(self, zigpy_device):
        Domoticz.Log("device_announce Zigpy Device: %s" %(zigpy_device))


    def device_initialized(self, device, *, new=True):
        # Called at runtime after a device's information has been queried.
        # I also call it on startup to load existing devices from the DB.

        LOGGER.info("Device is ready: new=%s, device=%s NwkId: %s IEEE: %s signature=%s", new, device, device.nwk, device._ieee, device.get_signature())   
        if new and device.nwk != 0x0000 and len( device.get_signature()) > 0:   
            Domoticz.Debug("Calling domoCreateDevice")
            device_signature = device.get_signature()
            if 'device_type' in device_signature:
                Domoticz.Debug("Device Type: %s (%s)" %(device_signature['device_type'], type(device_signature['device_type'])))
            domoCreateDevice( self, device._ieee, device.get_signature() )

        for ep_id, endpoint in device.endpoints.items():
            # Ignore ZDO
            if ep_id == 0:
                continue

            # You need to attach a listener to every cluster to receive events
            for cluster in endpoint.in_clusters.values():
                # The context listener passes its own object as the first argument
                # to the callback
                cluster.add_context_listener(self)


    #def device_left(self, device):
    #    pass


    #def device_removed(self, device):
    #    pass


    def cluster_command(self, cluster, command_id, *args):
        #Handle commands received to this cluster.
        # Each object is linked to its parent (i.e. app > device > endpoint > cluster)
        device = cluster.endpoint.device
        Domoticz.Log("cluster_command - Cluster: %s ClusterId: 0x%04x command_id: %s args: %s" %(cluster, cluster.cluster_id, command_id, args))


    def attribute_updated(self, cluster, attribute_id, value):
        # Each object is linked to its parent (i.e. app > device > endpoint > cluster)
        device = cluster.endpoint.device
        Domoticz.Debug("Device Signature: %s" %device.get_signature())
        Domoticz.Debug("Received an attribute update %s=%s on cluster %s from device %s/%s" %( attribute_id, value, cluster, device, device._ieee) )
        Domoticz.Debug("     - cluster: %s type: %s" %(cluster, type(cluster)))
        Domoticz.Debug("Cluster %04x Attribute: %s value: %s type(%s)" %(cluster.cluster_id, attribute_id, value, type(value)))
        domoMajDevice( self, device._ieee, cluster.cluster_id, attribute_id, value )

