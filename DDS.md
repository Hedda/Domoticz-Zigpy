# Detailed Design Specifications


## Purpose

Define the DDS of the Domoticz-Zigpy plugin based on the current proof of concept and trials


## High level

* zigpy is based on the asyncio python feature , with a number of blocking statement ( wait, sleep ... ) in the library, we have to run the zigpy layer on a dedicated thread.
* When the Domoticz plugin runs, it runs under 1 thread.
* Domoticz calls which read/update the Domoticz sqlite database, can be locked, so in order to give the responsivness to the zigpy layer it is important to decouple the 2.


### Threads

```
+--------------------------------------------------------------------------------------+
|                                                                                      |
|                          Domoticz Plugin ( BasePlugin )                                                            
|   onCommand                                                Device(Creation,Update)   |
+--------------------------------------------------------------------------------------+
      |                                                        ^
      |                                                        |
    +---+                                  +----------------------------------------+
    | Q | zigpy                            |                                        |
    +---+                                  |     Thread ( domo device management)   |
      |                                    |                                        |
      |                                    +----------------------------------------+
      |                                                       ^
      |                                                       |      
      |                                                     +---+
      |                                                     | Q | forwarder
      |                                                     +---+
      |                                                       |                                                     
      v                                                       :
+--------------------------------------------------------------------------------------+
|                                                                                      |
|     Thread ( Zigpy ) /  MainListener and management of actions (wip)                 |
|                                                                                      |
+--------------------------------------------------------------------------------------+                                  
```    


1. Main thread launched by Domoticz when the plugin is started
   1. Domoticz update (domo device management): 
      This thread will receive Queue messages request to update the various Domoticz "devices"
      This will serialize all messages and avoid any reentrance and ressource issues.
      
   1. Zigpy stack: This will handle the all Zigpy stack from Listener but also for handling Domoticz actions to be send to the zigbee objetcs. 
      This means that this thread can send Queue messages to the Domoticz update thread, but also can receive Queue message from Domoticz main thread ( onCommand)
      
      
      
### Queues

1. Queue: zigpy
   Will receive messages from Domoticz main thread, from the Web UI to get injected into zigpy for processing. 
   This could be actions on object ( On/Off, diming, color, setpoint ....)
   This could be remove an object from the Zigbee network
   This could be Radio related actions like Switch On/Off the ZiGate Led, Start a Neighbourg report, Change the Channel, Set Extended PanId ...
   
1. Queue: forwarder
   Will receive messages from zigpy layer to be handled by domo device management.
