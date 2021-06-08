# Zigpy plugin for Domoticz

With the recent change done in Domoticz, the issue arround SQLITE3 is now solved.

## Introduction

[Domoticz-Zigpy](https://github.com/zigpy/zigpy) is an integration project which goal is to implement hardware independent Zigbee support in [Domoticz](https://www.domoticz.com/) open source home automation software using the [https://github.com/zigpy/zigpy/ zigpy] Python library.

It is important to understand that zigpy is mainyly developped for Home Automation application, and in such I see a lot of push to get the application reproducing what HA is doing.

Zigbee integration via zigpy this way would allow users to directly connect one of many off-the-shelf Zigbee adapters from different manufacturers using one of the available Zigbee radio library modules compatible with the zigpy API to control Zigbee based devices, without the need for a third-party gateway/hub/bridge that needs to be managed separately. This can enable the use of the same common interface no matter which Zigbee hardware adapter that users have. 

The ultimate goal of zigpy (often also refered to as "zigpy library" or "zigpy project") is to be a free and open source software library that can interface with a Zigbee coordinator (sometimes referred to as a Zigbee controller) from any manufacturer and allow anyone who integrates zigpy to create applications to control devices on a Zigbee network, without requiring a very deep knowledge of the Zigbee specifications and manufacturer proprietary implementations.

The zigpy Github Organization is located at https://github.com/zigpy/. There are several repositories at that location. Their README of the main project , located in the https://github.com/zigpy/zigpy/ repository. This software is aimed at application developers who wish to incorporate or integrate Zigbee functionality into their applications. The project consists of the main zigpy library, wrappers for Zigbee radios from different manufacturers, and supporting projects, all written in Python.

## WARNING!!! - Work in progress

This project at this early stage is more a developers-only POC (Proof-Of-Concept) than anything else, as such users should not expect anything with it to work as of yet.


## Current issues

For now there are a number of show stoppers that need to be solved/sorted/fixed or have a more acceptable workaround before can move forward:

   * Zigpy library and quirk are developped for __Home Automation__ with no documentation on how to use. These are very focus on the HA design. Using Zigpy on Domoticz required a lot of work at that stage :
      1. Understand how to use zigpy
      2. Understand what to do in order to have a correct setup (inside the plugin) to get all events from devices
      
   * Zigpy has not a lot of manufacturer device support. During my work on the proof of concept, quiet a number of the devices that I am using often for my devlopement and tests where not full supported and created error messages. The end result would be for the current ZiGat users a lack of supported devices.
      * Aqara Opple Switches not supported
      * Xiaomi Vibration making errors
      * Legrand devices not supported (they leave the network after a while)
      * And even the manufacturer specific support do not take in consideration Binding and Configure Reporting 
   
   * The Zigate layer is not really mature and is at an early stage. That mean that we would not have such integration level with ZiGate as we have currently with the ZiGate plugin for Domoticz.
   

1. Required a lot of time to be spent in order to understand how the zigpy library .
2. debuging seems complex due to the zigpy lib with the embdeed python framework. For instance standard python error are not reported with a stack trace and line numbers where to find the issue, nor the full error description!


## TO BE ADDRESSED

* [IMPORTANT] Performance (response-time). The proof-of-concept implemenation has been developed with a LUMI Motion Sensor from Xiaomi/Aquara. This communicate 2 events ( Motion detection via Cluster 0x0406 and Illuminence via cluster 0x0400 ). 
  * This is using the "quirk" part (from [ZHA Device Handlers](https://github.com/zigpy/zha-device-handlers/)), and I do not fully understand how it works (especially in regards to that issue https://github.com/zigpy/zha-device-handlers/issues/469 - I do not understand what Cluster IAS should do here!)
  * But in general I found the performance not as expected. Quiet some lag between the Motion and the event reported into the plugin layer (not the Domoticz itself). The lag could be at several levels:
    * Maybea localized issue only with Xiaomi/Aquara LUMI devices? Maybe even localized issue only with battery-operated Xiaomi/Aquara LUMI devices?
    * zigpy-zigate as the implementation is quiet early?
    * Difference between the asyncio and the all zigpy stack in comparaison with the zigate plugin which is fully asynchrone with no waiting and synchronisation mecanism? From what I have measured with the zigate plugin the delay between receiving a message from the UART and getting the update on Domoticz widget is around 3ms. Here I have the impression that an important lag  between a motion should be detected, and the time the motion is seen by the app layer .
  * I had the impression that doing two pairing at the same time could be problematic - but need to be checked again, as I do not see why.

* zigpy provides a method call get_signature() which is available on the device object and provide a "device signature". In other words it gives in a python dictionary format informations like:
  * List of Endpoints
  * List of Cluster In and CLuster Out for each Endpoint
  
    

## LIMITATIONS

* Currently Zigpy library do not provide to interact directly with all the hardware features on a Zigbee radio. For instance in the context of the ZiGate coordinator:
  * Currently not posibility to reset the PDM and erase the all memory. That is a shame as this is quiet convenient to get a clean situation
  * Currently no access to the LED control
  * Currently no access to the Certification CE or FCC
  * Currently no access to the TX Power / Energy level
  * Currently no access to ZiGate reset ( which is quiet convenient when hang). The reset allow to reboot the Zigbee stack of the zigate without any break.
* the zha-quirks are Home Automation related and keep that in the naming as well as the packages delivered.
* the current library seems not to take care of the Bind and Configure Reporting of the devices during the pairing process. In result it is up to the above layer to do so. The consequences are tha such above layer has to take care of all manufacturer specifics for the Binding and Reporting parts while the Quirk does also for mapping Cluster/Attribute to a more standard thing. End result will be to manage twice customer specific actions !

* The current implementation of zigpy / quirks leave to the application layer to do all of the binding and configure reporting, which then required to manage the manufacturer specific device cases (which is alreday done at the quirks level). https://github.com/zigpy/zigpy/discussions/752 This doesn't make sense to have the plugin doing all of this ( bindings + configure reporting).

## Design Principle

https://github.com/pipiche38/Domoticz-Zigpy/blob/master/DDS.md





## Details on the Zigpy project

This project as such will rely on multiple radio libraries from the zigpy project as a dependency to interface 
with Zigbee radios which all aim to provide a coherent and consistent API in order among them to make it 
easier for integrations to support multiple adapters for different hardware manufacturers. For now though it 
is only being tested with the ZiGate hardware using the zigpy-zigate radio library.

- [bellows - zigpy radio library supporting Silicons Labs EmberZNet based Zigbee radios](https://github.com/zigpy/bellows)
- [zigpy-znp - zigpy radio library supporting newer Texas Instruments Z-Stack (CC2652 and CC1352) based Zigbee 
radios](https://github.com/zha-ng/zigpy-znp)
- [zigpy-deconz - zigpy radio library supporting dresden dlektronik deCONZ (ConBee and RaspBee) based Zigbee 
radios](https://github.com/zigpy/zigpy-deconz)
- [zigpy-xbee - zigpy radio library supporting XBee based Zigbee radios](https://github.com/zigpy/zigpy-xbee)
- [zigpy-zigate - zigpy radio library supporting ZiGate based Zigbee radios](https://github.com/zigpy/zigpy-zigate)

It addition it will utilize the zha-device-handlers (a.k.a. zha-quirks) library from the zigpy project as a 
dependency which will act as a tranaslator to try to handle individual Zigbee device exception and deviation 
handling for those Zigbee devices that do not fully conform to the standard specifications set by the Zigbee 
Alliance.

- <https://github.com/zigpy/zha-device-handlers>
