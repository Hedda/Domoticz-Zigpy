
import Domoticz
try:
    from Domoticz import Devices
except ImportError:
    pass

from Modules.domo_tools import get_type_from_cluster

def domoCreateDevice( self, device_ieee, device_signature):

    Domoticz.Debug("device_signature: %s" %device_signature)
    if 'model' in device_signature:
        Domoticz.Debug(" - Model: %s" %device_signature['model'])

    if 'node_desc' in device_signature:
        Domoticz.Debug(" - Node Desciptor: %s" %device_signature['node_desc'])

    if 'endpoints' in device_signature:
        device_signature_endpoint = device_signature[ 'endpoints']

    for ep in device_signature_endpoint:
        
        Domoticz.Debug(" --> ep: %s" %ep)
        in_cluster = device_signature_endpoint[ep]['input_clusters']
        out_cluster = device_signature_endpoint[ep]['output_clusters']
        for cluster in set(in_cluster+out_cluster):
            Domoticz.Debug("----> Cluster: %s" %cluster)
            widget_type = get_type_from_cluster( cluster )
            Domoticz.Debug("---------> Widget Type: %s" %widget_type)

            if widget_type is None:
                continue
        
            elif widget_type == 'Switch':
                Domoticz.Debug("----> Create Switch")
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 244, Subtype_ = 73, Switchtype_ = 0 )

            elif widget_type == 'Lux':
                Domoticz.Debug("----> Create Lux")
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 246, Subtype_ = 1, Switchtype_ = 0 )
                
            elif widget_type == 'Motion':
                Domoticz.Debug("----> Create Motion")
                createDomoticzWidget( self, device_ieee, ep, widget_type, widgetType='Motion')

            elif widget_type == 'Temp':
                createDomoticzWidget( self, device_ieee, ep, widget_type, widgetType="Temperature")

            elif widget_type == 'Humi':
                createDomoticzWidget( self, device_ieee, ep, widget_type, widgetType="Humidity")

            elif widget_type == 'Baro':
                createDomoticzWidget( self, device_ieee, ep, widget_type, widgetType="Barometer")

            elif widget_type == 'Venetian':
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 244, Subtype_ = 73, Switchtype_ = 15 )

            elif widget_type == 'LvlControl':
                createDomoticzWidget( self, device_ieee, ep, widget_type, Type_ = 244, Subtype_ = 73, Switchtype_ = 7 )
 
def createDomoticzWidget( self, ieee, ep, cType, widgetType = None,
                         Type_ = None, Subtype_ = None, Switchtype_ = None ): 

    Domoticz.Debug("createDomoticzWidget")
    unit = getFreeUnit(self)
    Domoticz.Debug("--> Unit: %s" %unit)
    widgetName = '%s %s - %s' %(cType, ieee, ep )
    Domoticz.Debug("--> widgetName: %s" %widgetName)
    if widgetType:
        Domoticz.Log("Creating device is Domoticz DeviceID:%s Name: %s Unit: %s TypeName: %s" %(ieee, widgetName, unit, widgetType))
        myDev = Domoticz.Device( DeviceID = str(ieee), Name = widgetName, Unit = unit, TypeName = widgetType )

    elif Type_ is not None and Subtype_ is not None and Switchtype_ is not None:
        myDev = Domoticz.Device( DeviceID = str(ieee), Name = widgetName, Unit = unit, Type = Type_, Subtype = Subtype_, Switchtype = Switchtype_ )

    else:
        Domoticz.Error("createDomoticzWidget cannot create widget for %s" %(widgetName))
        return
    
    myDev.Create()
    ID = myDev.ID
    if myDev.ID == -1 :
        Domoticz.Error("Domoticz widget creation failed. Check that Domoticz can Accept New Hardware [%s]" %myDev )



def getFreeUnit(self, nbunit_=1):
    '''
    FreeUnit
    Look for a Free Unit number. If nbunit > 1 then we look for nbunit consecutive slots
    '''
    Domoticz.Debug("getFreeUnit - Devices: %s" %len(self.domoticzDevices))
    
    for x in range(1,255):
        if x not in self.domoticzDevices and nbunit_ == 1:
            return x

        elif x not in self.domoticzDevices:
            nb = 1
            for y in range(x+1, 255):
                if y in self.domoticzDevices:
                    break
                nb += 1
                if nb == nbunit_: # We have found nbunit consecutive slots
                    self.log.logging("Widget", "Debug", "FreeUnit - device " + str(x) + " available")
                    return x

    return len(self.domoticzDevices) + 1

