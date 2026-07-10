# 📊 ANTA Report <a id="anta-report"></a>

**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
    - [Summary Totals](#summary-totals)
    - [Summary Totals Device Under Test](#summary-totals-device-under-test)
    - [Summary Totals Per Category](#summary-totals-per-category)
  - [Test Results](#test-results)

## 📉 Test Results Summary <a id="test-results-summary"></a>

### 🔢 Summary Totals <a id="summary-totals"></a>

| Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error |
| :- | :- | :- | :- | :- |
| 186 | 120 | 42 | 24 | 0 |

### 🔌 Summary Totals Device Under Test <a id="summary-totals-device-under-test"></a>

| Device | Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error | Categories Skipped | Categories Failed |
| :- | :- | :- | :- | :- | :- | :- | :- |
| **s1-leaf1** | 33 | 22 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |
| **s1-leaf2** | 33 | 22 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |
| **s1-leaf3** | 33 | 22 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |
| **s1-leaf4** | 33 | 22 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |
| **s1-spine1** | 27 | 16 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |
| **s1-spine2** | 27 | 16 | 7 | 4 | 0 | Hardware | Configuration, Logging, System |

### 🗂️ Summary Totals Per Category <a id="summary-totals-per-category"></a>

| Test Category | Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error |
| :- | :- | :- | :- | :- | :- |
| **BGP** | 6 | 6 | 0 | 0 | 0 |
| **Configuration** | 12 | 6 | 0 | 6 | 0 |
| **Connectivity** | 12 | 12 | 0 | 0 | 0 |
| **Hardware** | 42 | 0 | 42 | 0 | 0 |
| **Interfaces** | 38 | 38 | 0 | 0 | 0 |
| **Logging** | 6 | 0 | 0 | 6 | 0 |
| **MLAG** | 12 | 12 | 0 | 0 | 0 |
| **Routing** | 6 | 6 | 0 | 0 | 0 |
| **STP** | 6 | 6 | 0 | 0 | 0 |
| **System** | 42 | 30 | 0 | 12 | 0 |
| **VXLAN** | 4 | 4 | 0 | 0 | 0 |

## 🧪 Test Results <a id="test-results"></a>

| Device | Categories | Test | Description | Result | Messages |
| :- | :- | :- | :- | :- | :- |
| s1-leaf1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-leaf1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:47 3b006ad3b2a5 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-leaf1 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.87% |
| s1-leaf2 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-leaf2 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:50 454caa1291b1 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf2 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-leaf2 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.74% |
| s1-leaf3 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-leaf3 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:52 1e52b42f5b70 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf3 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-leaf3 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.76% |
| s1-leaf4 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-leaf4 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:53 eb6059e6c4c9 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf4 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-leaf4 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.78% |
| s1-spine1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-spine1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:42 1c3d23c55bd7 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-spine1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-spine1 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.76% |
| s1-spine2 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ❌&nbsp;Failure | --- flash:/startup-config<br>+++ system:/running-config<br>@@ -8,6 +8,9 @@<br> !<br> management api http-commands<br>    no shutdown<br>+   !<br>+   vrf default<br>+      no shutdown<br> !<br> daemon TerminAttr<br>    exec /usr/bin/TerminAttr -cvcompression=gzip -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -cvaddr=192.168.0.5:9910 -cvauth=token,/tmp/token -cvvrf=default -taillogs -disableaaa<br> |
| s1-spine2 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Jul 10 02:38:45 ea21b51d2a2f NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-spine2 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ❌&nbsp;Failure | Mount point: overlay          60G   45G   15G  76% / - Higher disk space utilization - Expected: 75% Actual: 76%<br>Mount point: /dev/sda2        60G   45G   15G  76% /mnt/flash - Higher disk space utilization - Expected: 75% Actual: 76% |
| s1-spine2 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 85.99% |
| s1-leaf1 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-leaf1 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-leaf2 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-leaf3 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-leaf4 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-spine1 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-spine2 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-leaf1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf1 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-leaf1 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-leaf1 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-leaf1 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-leaf1 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf1 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-leaf1 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-leaf1 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-leaf1 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf1 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf2 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf2 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-leaf2 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-leaf2 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-leaf2 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-leaf2 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf2 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-leaf2 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-leaf2 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-leaf2 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf2 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf3 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf3 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-leaf3 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-leaf3 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-leaf3 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-leaf3 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf3 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-leaf3 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-leaf3 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-leaf3 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf3 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf4 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf4 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-leaf4 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-leaf4 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-leaf4 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-leaf4 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf4 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-leaf4 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-leaf4 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-leaf4 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf4 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-spine1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-spine1 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-spine1 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-spine1 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-spine1 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-spine1 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-spine1 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-spine1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-spine1 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-spine1 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-spine1 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-spine2 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-spine2 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-spine2 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-spine2 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-spine2 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-spine2 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-spine2 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-spine2 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-spine2 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-spine2 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-spine2 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
