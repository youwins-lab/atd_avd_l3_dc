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
| 252 | 180 | 56 | 16 | 0 |

### 🔌 Summary Totals Device Under Test <a id="summary-totals-device-under-test"></a>

| Device | Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error | Categories Skipped | Categories Failed |
| :- | :- | :- | :- | :- | :- | :- | :- |
| **s1-brdr1** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-brdr2** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-leaf1** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-leaf2** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-leaf3** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-leaf4** | 33 | 24 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-spine1** | 27 | 18 | 7 | 2 | 0 | Hardware | Logging, System |
| **s1-spine2** | 27 | 18 | 7 | 2 | 0 | Hardware | Logging, System |

### 🗂️ Summary Totals Per Category <a id="summary-totals-per-category"></a>

| Test Category | Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error |
| :- | :- | :- | :- | :- | :- |
| **BGP** | 8 | 8 | 0 | 0 | 0 |
| **Configuration** | 16 | 16 | 0 | 0 | 0 |
| **Connectivity** | 16 | 16 | 0 | 0 | 0 |
| **Hardware** | 56 | 0 | 56 | 0 | 0 |
| **Interfaces** | 52 | 52 | 0 | 0 | 0 |
| **Logging** | 8 | 0 | 0 | 8 | 0 |
| **MLAG** | 18 | 18 | 0 | 0 | 0 |
| **Routing** | 8 | 8 | 0 | 0 | 0 |
| **STP** | 8 | 8 | 0 | 0 | 0 |
| **System** | 56 | 48 | 0 | 8 | 0 |
| **VXLAN** | 6 | 6 | 0 | 0 | 0 |

## 🧪 Test Results <a id="test-results"></a>

| Device | Categories | Test | Description | Result | Messages |
| :- | :- | :- | :- | :- | :- |
| s1-brdr1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:51 f191788625ab NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> Nov  1 07:30:32 s1-brdr1 Bgp: %BGP-3-NOTIFICATION: sent to neighbor 192.1.1.3 (VRF default AS 65099) 6/7 (Cease/connection collision resolution) 0 bytes <br> <br> |
| s1-brdr1 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 93.31% |
| s1-brdr2 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:53 6442f3bb6a64 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> Nov  1 07:30:32 s1-brdr2 Bgp: %BGP-3-NOTIFICATION: sent to neighbor 192.1.1.2 (VRF default AS 65099) 6/7 (Cease/connection collision resolution) 0 bytes <br> <br> |
| s1-brdr2 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.77% |
| s1-leaf1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:40 b1b88c9e0e56 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf1 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 93.31% |
| s1-leaf2 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:42 ac478a0a1309 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf2 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.62% |
| s1-leaf3 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:44 cbe516a7c5f9 NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf3 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.83% |
| s1-leaf4 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:45 889ff1464dfd NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-leaf4 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.63% |
| s1-spine1 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:37 0d4f8e4f3dbe NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-spine1 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.83% |
| s1-spine2 | Logging | VerifyLoggingErrors | Verifies there are no syslog messages with a severity of ERRORS or higher. | ❌&nbsp;Failure | Device has reported syslog messages with a severity of ERRORS or higher:<br>Nov  1 07:17:38 b75e422355cc NorCalInit: %HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system<br> <br> |
| s1-spine2 | System | VerifyMemoryUtilization | Verifies whether the memory utilization is below 75%. | ❌&nbsp;Failure | Device has reported a high memory usage - Expected: < 75% Actual: 92.89% |
| s1-brdr1 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-brdr1 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyEnvironmentCooling | Verifies the status of power supply fans and all fan trays. | ⏭️&nbsp;Skipped | VerifyEnvironmentCooling test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyEnvironmentPower | Verifies the power supplies state and input voltage. | ⏭️&nbsp;Skipped | VerifyEnvironmentPower test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyEnvironmentSystemCooling | Verifies the device's system cooling status. | ⏭️&nbsp;Skipped | VerifyEnvironmentSystemCooling test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyInventory | Verifies the physical hardware inventory of the device. | ⏭️&nbsp;Skipped | VerifyInventory test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyTemperature | Verifies if the device temperature is within acceptable limits. | ⏭️&nbsp;Skipped | VerifyTemperature test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyTransceiversManufacturers | Verifies if all the transceivers come from approved manufacturers. | ⏭️&nbsp;Skipped | VerifyTransceiversManufacturers test is not supported on cEOSLab |
| s1-brdr2 | Hardware | VerifyTransceiversTemperature | Verifies if all the transceivers are operating at an acceptable temperature. | ⏭️&nbsp;Skipped | VerifyTransceiversTemperature test is not supported on cEOSLab |
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
| s1-brdr1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-brdr1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
| s1-brdr1 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-brdr1 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-brdr1 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-brdr1 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-brdr1 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-brdr1 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-brdr1 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-brdr1 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-brdr1 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-brdr1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-brdr1 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-brdr2 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-brdr2 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
| s1-brdr2 | Configuration | VerifyZeroTouch | Verifies ZeroTouch is disabled. | ✅&nbsp;Success | - |
| s1-brdr2 | Connectivity | VerifyLLDPNeighbors | Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors. | ✅&nbsp;Success | - |
| s1-brdr2 | Connectivity | VerifyReachability | Verifies point-to-point reachability between Ethernet interfaces. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyIllegalLACP | Verifies there are no illegal LACP packets in port channels. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyInterfaceDiscards | Verifies that the interfaces packet discard counters are equal to zero. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyInterfaceErrDisabled | Verifies there are no interfaces in the errdisabled state. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyInterfaceErrors | Verifies that the interfaces error counters are equal to zero. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyInterfaceUtilization | Verifies that the utilization of interfaces is below a certain threshold. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyInterfacesStatus | Verifies the operational states of specified interfaces to ensure they match expected configurations. | ✅&nbsp;Success | - |
| s1-brdr2 | Interfaces | VerifyPortChannels | Verifies there are no inactive ports in port channels. | ✅&nbsp;Success | - |
| s1-brdr2 | MLAG | VerifyMlagConfigSanity | Verifies there are no MLAG config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-brdr2 | MLAG | VerifyMlagInterfaces | Verifies there are no inactive or active-partial MLAG ports. | ✅&nbsp;Success | - |
| s1-brdr2 | MLAG | VerifyMlagStatus | Verifies the health status of the MLAG configuration. | ✅&nbsp;Success | - |
| s1-brdr2 | Routing | VerifyRoutingProtocolModel | Verifies the configured routing protocol model. | ✅&nbsp;Success | - |
| s1-brdr2 | STP | VerifySTPCounters | Verifies there is no errors in STP BPDU packets. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyAgentLogs | Verifies there are no agent crash reports. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyCoredump | Verifies there are no core dump files. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-brdr2 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-brdr2 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-leaf1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf1 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf2 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf2 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-leaf2 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf2 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf2 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf3 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf3 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-leaf3 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf3 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf3 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-leaf4 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-leaf4 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-leaf4 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-leaf4 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-leaf4 | VXLAN | VerifyVxlanConfigSanity | Verifies there are no VXLAN config-sanity inconsistencies. | ✅&nbsp;Success | - |
| s1-spine1 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-spine1 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-spine1 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-spine1 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
| s1-spine2 | BGP | VerifyBGPPeerSession | Verifies the session state of BGP peers. | ✅&nbsp;Success | - |
| s1-spine2 | Configuration | VerifyRunningConfigDiffs | Verifies there is no difference between the running-config and the startup-config. | ✅&nbsp;Success | - |
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
| s1-spine2 | System | VerifyFileSystemUtilization | Verifies that no partition is utilizing more than 75% of its disk space. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyMaintenance | Verifies that the device is not currently under or entering maintenance. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyNTP | Verifies if NTP is synchronised. | ✅&nbsp;Success | - |
| s1-spine2 | System | VerifyReloadCause | Verifies the last reload cause of the device. | ✅&nbsp;Success | - |
