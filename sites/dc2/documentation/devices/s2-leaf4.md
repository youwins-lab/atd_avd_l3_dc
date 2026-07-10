# s2-leaf4

## Table of Contents

- [Management](#management)
  - [Management Interfaces](#management-interfaces)
  - [Management API HTTP](#management-api-http)
- [Authentication](#authentication)
  - [Enable Password](#enable-password)
- [MLAG](#mlag)
  - [MLAG Summary](#mlag-summary)
  - [MLAG Device Configuration](#mlag-device-configuration)
- [Spanning Tree](#spanning-tree)
  - [Spanning Tree Summary](#spanning-tree-summary)
  - [Spanning Tree Device Configuration](#spanning-tree-device-configuration)
- [Internal VLAN Allocation Policy](#internal-vlan-allocation-policy)
  - [Internal VLAN Allocation Policy Summary](#internal-vlan-allocation-policy-summary)
  - [Internal VLAN Allocation Policy Device Configuration](#internal-vlan-allocation-policy-device-configuration)
- [VLANs](#vlans)
  - [VLANs Summary](#vlans-summary)
  - [VLANs Device Configuration](#vlans-device-configuration)
- [Interfaces](#interfaces)
  - [Ethernet Interfaces](#ethernet-interfaces)
  - [Port-Channel Interfaces](#port-channel-interfaces)
  - [Loopback Interfaces](#loopback-interfaces)
  - [VLAN Interfaces](#vlan-interfaces)
  - [VXLAN Interface](#vxlan-interface)
- [Routing](#routing)
  - [Service Routing Protocols Model](#service-routing-protocols-model)
  - [Virtual Router MAC Address](#virtual-router-mac-address)
  - [IP Routing](#ip-routing)
  - [IPv6 Routing](#ipv6-routing)
  - [Static Routes](#static-routes)
  - [Router BGP](#router-bgp)
- [BFD](#bfd)
  - [Router BFD](#router-bfd)
- [Multicast](#multicast)
  - [IP IGMP Snooping](#ip-igmp-snooping)
- [Filters](#filters)
  - [Prefix-lists](#prefix-lists)
  - [Route-maps](#route-maps)
- [VRF Instances](#vrf-instances)
  - [VRF Instances Summary](#vrf-instances-summary)
  - [VRF Instances Device Configuration](#vrf-instances-device-configuration)

## Management

### Management Interfaces

#### Management Interfaces Summary

##### IPv4

| Management Interface | Description | Type | VRF | IP Address | Gateway |
| -------------------- | ----------- | ---- | --- | ---------- | ------- |
| Management0 | OOB_MANAGEMENT | oob | default | 192.168.0.25/24 | 192.168.0.1 |

##### IPv6

| Management Interface | Description | Type | VRF | IPv6 Address | IPv6 Gateway | ND RA Disabled | ND RA RX Accept | ND Managed Config Flag | ND Other Config Flag | ND Cache | ND RA DNS Servers |
| -------------------- | ----------- | ---- | --- | ------------ | ------------ | -------------- | --------------- | ---------------------- | -------------------- | -------- | ----------------- |
| Management0 | OOB_MANAGEMENT | oob | default | - | - | - | - | - | - | - | - |

#### Management Interfaces Device Configuration

```eos
!
interface Management0
   description OOB_MANAGEMENT
   no shutdown
   ip address 192.168.0.25/24
```

### Management API HTTP

#### Management API HTTP Summary

| HTTP | HTTPS | UNIX-Socket | Default Services | Session Timeout |
| ---- | ----- | ----------- | ---------------- | --------------- |
| False | True | - | - | 1440 minutes |

#### Management API VRF Access

| VRF Name | IPv4 ACL | IPv6 ACL |
| -------- | -------- | -------- |
| default | - | - |

#### Management API HTTP Device Configuration

```eos
!
management api http-commands
   protocol https
   no shutdown
   !
   vrf default
      no shutdown
```

## Authentication

### Enable Password

Enable password has been disabled

## MLAG

### MLAG Summary

| Domain-id | Local-interface | Peer-address | Peer-link |
| --------- | --------------- | ------------ | --------- |
| LeafPair2 | Vlan4094 | 192.0.0.228 | Port-Channel1000 |

Dual primary detection is disabled.

### MLAG Device Configuration

```eos
!
mlag configuration
   domain-id LeafPair2
   local-interface Vlan4094
   peer-address 192.0.0.228
   peer-link Port-Channel1000
```

## Spanning Tree

### Spanning Tree Summary

STP mode: **rapid-pvst**

#### Rapid-PVST Instance and Priority

| Instance(s) | Priority |
| -------- | -------- |
| 1-4094 | 0 |

#### Global Spanning-Tree Settings

- Spanning Tree disabled for VLANs: **4093-4094**
- Global BPDU Guard for Edge ports is enabled.

### Spanning Tree Device Configuration

```eos
!
spanning-tree mode rapid-pvst
no spanning-tree vlan-id 4093-4094
spanning-tree edge-port bpduguard default
spanning-tree vlan-id 1-4094 priority 0
```

## Internal VLAN Allocation Policy

### Internal VLAN Allocation Policy Summary

| Policy Allocation | Range Beginning | Range Ending |
| ----------------- | --------------- | ------------ |
| ascending | 1006 | 1199 |

### Internal VLAN Allocation Policy Device Configuration

```eos
!
vlan internal order ascending range 1006 1199
```

## VLANs

### VLANs Summary

| VLAN ID | Name | Trunk Groups |
| ------- | ---- | ------------ |
| 10 | ten | - |
| 20 | twenty | - |
| 4001 | MLAG_L3_VRF_A | MLAG |
| 4093 | MLAG_L3 | MLAG |
| 4094 | MLAG | MLAG |

### VLANs Device Configuration

```eos
!
vlan 10
   name ten
!
vlan 20
   name twenty
!
vlan 4001
   name MLAG_L3_VRF_A
   trunk group MLAG
!
vlan 4093
   name MLAG_L3
   trunk group MLAG
!
vlan 4094
   name MLAG
   trunk group MLAG
```

## Interfaces

### Ethernet Interfaces

#### Ethernet Interfaces Summary

##### L2

| Interface | Description | Mode | VLANs | Native VLAN | Trunk Group | Channel-Group |
| --------- | ----------- | ---- | ----- | ----------- | ----------- | ------------- |
| Ethernet1 | MLAG_s2-leaf3_Ethernet1 | *trunk | *- | *- | *MLAG | 1000 |
| Ethernet4 | SERVER_s2-host2_Ethernet2 | *trunk | *10,20 | *- | *- | 4 |
| Ethernet6 | MLAG_s2-leaf3_Ethernet6 | *trunk | *- | *- | *MLAG | 1000 |

*Inherited from Port-Channel Interface

##### IPv4

| Interface | Description | Channel Group | IP Address | VRF | MTU | Shutdown | ACL In | ACL Out |
| --------- | ----------- | ------------- | ---------- | --- | --- | -------- | ------ | ------- |
| Ethernet2 | P2P_s2-spine1_Ethernet5 | - | 10.255.1.209/31 | default | 9214 | False | - | - |
| Ethernet3 | P2P_s2-spine2_Ethernet5 | - | 10.255.1.211/31 | default | 9214 | False | - | - |

#### Ethernet Interfaces Device Configuration

```eos
!
interface Ethernet1
   description MLAG_s2-leaf3_Ethernet1
   no shutdown
   channel-group 1000 mode active
!
interface Ethernet2
   description P2P_s2-spine1_Ethernet5
   no shutdown
   mtu 9214
   no switchport
   ip address 10.255.1.209/31
!
interface Ethernet3
   description P2P_s2-spine2_Ethernet5
   no shutdown
   mtu 9214
   no switchport
   ip address 10.255.1.211/31
!
interface Ethernet4
   description SERVER_s2-host2_Ethernet2
   no shutdown
   channel-group 4 mode active
!
interface Ethernet6
   description MLAG_s2-leaf3_Ethernet6
   no shutdown
   channel-group 1000 mode active
```

### Port-Channel Interfaces

#### Port-Channel Interfaces Summary

##### L2

| Interface | Description | Mode | VLANs | Native VLAN | Trunk Group | LACP Fallback Timeout | LACP Fallback Mode | MLAG ID | EVPN ESI |
| --------- | ----------- | ---- | ----- | ----------- | ----------- | --------------------- | ------------------ | ------- | -------- |
| Port-Channel4 | SERVER_s2-host2 | trunk | 10,20 | - | - | - | - | 4 | - |
| Port-Channel1000 | MLAG_s2-leaf3_Port-Channel1000 | trunk | - | - | MLAG | - | - | - | - |

#### Port-Channel Interfaces Device Configuration

```eos
!
interface Port-Channel4
   description SERVER_s2-host2
   no shutdown
   switchport trunk allowed vlan 10,20
   switchport mode trunk
   switchport
   mlag 4
!
interface Port-Channel1000
   description MLAG_s2-leaf3_Port-Channel1000
   no shutdown
   switchport mode trunk
   switchport trunk group MLAG
   switchport
```

### Loopback Interfaces

#### Loopback Interfaces Summary

##### IPv4

| Interface | Description | VRF | IP Address |
| --------- | ----------- | --- | ---------- |
| Loopback0 | ROUTER_ID | default | 10.1.0.117/32 |
| Loopback1 | VXLAN_TUNNEL_SOURCE | default | 10.1.1.115/32 |

##### IPv6

| Interface | Description | VRF | IPv6 Addresses |
| --------- | ----------- | --- | -------------- |
| Loopback0 | ROUTER_ID | default | - |
| Loopback1 | VXLAN_TUNNEL_SOURCE | default | - |

#### Loopback Interfaces Device Configuration

```eos
!
interface Loopback0
   description ROUTER_ID
   no shutdown
   ip address 10.1.0.117/32
!
interface Loopback1
   description VXLAN_TUNNEL_SOURCE
   no shutdown
   ip address 10.1.1.115/32
```

### VLAN Interfaces

#### VLAN Interfaces Summary

| Interface | Description | VRF | MTU | Shutdown |
| --------- | ----------- | --- | --- | -------- |
| Vlan10 | ten | A | 9014 | False |
| Vlan20 | twenty | A | 9014 | False |
| Vlan4001 | MLAG_L3_VRF_A | A | 9214 | False |
| Vlan4093 | MLAG_L3 | default | 9214 | False |
| Vlan4094 | MLAG | default | 9214 | False |

##### IPv4

| Interface | VRF | IP Address | IP Address Virtual | IP Router Virtual Address | ACL In | ACL Out |
| --------- | --- | ---------- | ------------------ | ------------------------- | ------ | ------- |
| Vlan10 | A | - | 10.10.10.1/24 | - | - | - |
| Vlan20 | A | - | 10.20.20.1/24 | - | - | - |
| Vlan4001 | A | 192.2.2.229/31 | - | - | - | - |
| Vlan4093 | default | 192.1.1.229/31 | - | - | - | - |
| Vlan4094 | default | 192.0.0.229/31 | - | - | - | - |

#### VLAN Interfaces Device Configuration

```eos
!
interface Vlan10
   description ten
   no shutdown
   mtu 9014
   vrf A
   ip address virtual 10.10.10.1/24
!
interface Vlan20
   description twenty
   no shutdown
   mtu 9014
   vrf A
   ip address virtual 10.20.20.1/24
!
interface Vlan4001
   description MLAG_L3_VRF_A
   no shutdown
   mtu 9214
   vrf A
   ip address 192.2.2.229/31
!
interface Vlan4093
   description MLAG_L3
   no shutdown
   mtu 9214
   ip address 192.1.1.229/31
!
interface Vlan4094
   description MLAG
   no shutdown
   mtu 9214
   no autostate
   ip address 192.0.0.229/31
```

### VXLAN Interface

#### VXLAN Interface Summary

| Setting | Value |
| ------- | ----- |
| Source Interface | Loopback1 |
| UDP port | 4789 |
| EVPN MLAG Shared Router MAC | mlag-system-id |

##### VLAN to VNI, Flood List and Multicast Group Mappings

| VLAN | VNI | Flood List | Multicast Group |
| ---- | --- | ---------- | --------------- |
| 10 | 10010 | - | - |
| 20 | 10020 | - | - |

##### VRF to VNI and Multicast Group Mappings

| VRF | VNI | Overlay Multicast Group to Encap Mappings |
| --- | --- | ----------------------------------------- |
| A | 50001 | - |

#### VXLAN Interface Device Configuration

```eos
!
interface Vxlan1
   description s2-leaf4_VTEP
   vxlan source-interface Loopback1
   vxlan virtual-router encapsulation mac-address mlag-system-id
   vxlan udp-port 4789
   vxlan vlan 10 vni 10010
   vxlan vlan 20 vni 10020
   vxlan vrf A vni 50001
```

## Routing

### Service Routing Protocols Model

Multi agent routing protocol model enabled

```eos
!
service routing protocols model multi-agent
```

### Virtual Router MAC Address

#### Virtual Router MAC Address Summary

Virtual Router MAC Address: 00:1c:73:00:00:01

#### Virtual Router MAC Address Device Configuration

```eos
!
ip virtual-router mac-address 00:1c:73:00:00:01
```

### IP Routing

#### IP Routing Summary

| VRF | Routing Enabled |
| --- | --------------- |
| default | True |
| A | True |

#### IP Routing Device Configuration

```eos
!
ip routing
ip routing vrf A
```

### IPv6 Routing

#### IPv6 Routing Summary

| VRF | Routing Enabled |
| --- | --------------- |
| default | False |
| A | false |
| default | false |

### Static Routes

#### Static Routes Summary

| VRF | Destination Prefix | Next Hop IP | Exit interface | Administrative Distance | Tag | Route Name | Metric |
| --- | ------------------ | ----------- | -------------- | ----------------------- | --- | ---------- | ------ |
| default | 0.0.0.0/0 | 192.168.0.1 | - | 1 | - | - | - |

#### Static Routes Device Configuration

```eos
!
ip route 0.0.0.0/0 192.168.0.1
```

### Router BGP

ASN Notation: asplain

#### Router BGP Summary

| BGP AS | Router ID |
| ------ | --------- |
| 65102 | 10.1.0.117 |

| BGP Tuning |
| ---------- |
| no bgp default ipv4-unicast |
| distance bgp 20 200 200 |
| neighbor default send-community |
| graceful-restart restart-time 300 |
| graceful-restart |
| update wait-install |
| no bgp default ipv4-unicast |
| maximum-paths 4 |

#### Router BGP Peer Groups

##### EVPN-OVERLAY-LOCAL-PEERS

| Settings | Value |
| -------- | ----- |
| Address Family | evpn |
| Source | Loopback0 |
| BFD | True |
| Ebgp multihop | 3 |
| Send community | all |
| Maximum routes | 0 (no limit) |

##### IPV4-UNDERLAY-PEERS

| Settings | Value |
| -------- | ----- |
| Address Family | ipv4 |
| Send community | all |
| Maximum routes | 256000 |

##### MLAG-IPV4-UNDERLAY-PEER

| Settings | Value |
| -------- | ----- |
| Address Family | ipv4 |
| Remote AS | 65102 |
| Next-hop self | True |
| Send community | all |
| Maximum routes | 256000 |

#### BGP Neighbors

| Neighbor | Remote AS | VRF | Shutdown | Send-community | Maximum-routes | Allowas-in | BFD | RIB Pre-Policy Retain | Route-Reflector Client | Passive | TTL Max Hops |
| -------- | --------- | --- | -------- | -------------- | -------------- | ---------- | --- | --------------------- | ---------------------- | ------- | ------------ |
| 10.1.0.110 | 65100 | default | - | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | - | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | - | - | - | - |
| 10.1.0.112 | 65100 | default | - | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | - | Inherited from peer group EVPN-OVERLAY-LOCAL-PEERS | - | - | - | - |
| 10.255.1.208 | 65100 | default | - | Inherited from peer group IPV4-UNDERLAY-PEERS | Inherited from peer group IPV4-UNDERLAY-PEERS | - | - | - | - | - | - |
| 10.255.1.210 | 65100 | default | - | Inherited from peer group IPV4-UNDERLAY-PEERS | Inherited from peer group IPV4-UNDERLAY-PEERS | - | - | - | - | - | - |
| 192.1.1.228 | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | default | - | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | - | - | - | - | - | - |
| 192.2.2.228 | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | A | - | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | Inherited from peer group MLAG-IPV4-UNDERLAY-PEER | - | - | - | - | - | - |

#### Router BGP EVPN Address Family

- VPN import pruning is **enabled**

##### EVPN Peer Groups

| Peer Group | Activate | Route-map In | Route-map Out | Peer-tag In | Peer-tag Out | Encapsulation | Next-hop-self Source Interface |
| ---------- | -------- | ------------ | ------------- | ----------- | ------------ | ------------- | ------------------------------ |
| EVPN-OVERLAY-LOCAL-PEERS | True | - | - | - | - | default | - |

#### Router BGP VLANs

| VLAN | Route-Distinguisher | Both Route-Target | Import Route Target | Export Route-Target | Redistribute |
| ---- | ------------------- | ----------------- | ------------------- | ------------------- | ------------ |
| 10 | 10.1.0.117:10010 | 10010:10010 | - | - | learned |
| 20 | 10.1.0.117:10020 | 10020:10020 | - | - | learned |

#### Router BGP VRFs

| VRF | Route-Distinguisher | Redistribute | Graceful Restart |
| --- | ------------------- | ------------ | ---------------- |
| A | 10.1.0.117:50001 | connected | - |

#### Router BGP Device Configuration

```eos
!
router bgp 65102
   router-id 10.1.0.117
   update wait-install
   no bgp default ipv4-unicast
   maximum-paths 4
   no bgp default ipv4-unicast
   distance bgp 20 200 200
   neighbor default send-community
   graceful-restart restart-time 300
   graceful-restart
   neighbor EVPN-OVERLAY-LOCAL-PEERS peer group
   neighbor EVPN-OVERLAY-LOCAL-PEERS update-source Loopback0
   neighbor EVPN-OVERLAY-LOCAL-PEERS bfd
   neighbor EVPN-OVERLAY-LOCAL-PEERS ebgp-multihop 3
   neighbor EVPN-OVERLAY-LOCAL-PEERS password 7 <removed>
   neighbor EVPN-OVERLAY-LOCAL-PEERS send-community
   neighbor EVPN-OVERLAY-LOCAL-PEERS maximum-routes 0
   neighbor IPV4-UNDERLAY-PEERS peer group
   neighbor IPV4-UNDERLAY-PEERS password 7 <removed>
   neighbor IPV4-UNDERLAY-PEERS send-community
   neighbor IPV4-UNDERLAY-PEERS maximum-routes 256000
   neighbor MLAG-IPV4-UNDERLAY-PEER peer group
   neighbor MLAG-IPV4-UNDERLAY-PEER remote-as 65102
   neighbor MLAG-IPV4-UNDERLAY-PEER next-hop-self
   neighbor MLAG-IPV4-UNDERLAY-PEER description s2-leaf3
   neighbor MLAG-IPV4-UNDERLAY-PEER route-map RM-MLAG-PEER-IN in
   neighbor MLAG-IPV4-UNDERLAY-PEER password 7 <removed>
   neighbor MLAG-IPV4-UNDERLAY-PEER send-community
   neighbor MLAG-IPV4-UNDERLAY-PEER maximum-routes 256000
   neighbor 10.1.0.110 peer group EVPN-OVERLAY-LOCAL-PEERS
   neighbor 10.1.0.110 remote-as 65100
   neighbor 10.1.0.110 description s2-spine1_Loopback0
   neighbor 10.1.0.112 peer group EVPN-OVERLAY-LOCAL-PEERS
   neighbor 10.1.0.112 remote-as 65100
   neighbor 10.1.0.112 description s2-spine2_Loopback0
   neighbor 10.255.1.208 peer group IPV4-UNDERLAY-PEERS
   neighbor 10.255.1.208 remote-as 65100
   neighbor 10.255.1.208 description s2-spine1_Ethernet5
   neighbor 10.255.1.210 peer group IPV4-UNDERLAY-PEERS
   neighbor 10.255.1.210 remote-as 65100
   neighbor 10.255.1.210 description s2-spine2_Ethernet5
   neighbor 192.1.1.228 peer group MLAG-IPV4-UNDERLAY-PEER
   neighbor 192.1.1.228 description s2-leaf3_Vlan4093
   redistribute connected route-map RM-CONN-2-BGP
   !
   vlan 10
      rd 10.1.0.117:10010
      route-target both 10010:10010
      redistribute learned
   !
   vlan 20
      rd 10.1.0.117:10020
      route-target both 10020:10020
      redistribute learned
   !
   address-family evpn
      neighbor EVPN-OVERLAY-LOCAL-PEERS activate
      route import match-failure action discard
   !
   address-family ipv4
      no neighbor EVPN-OVERLAY-LOCAL-PEERS activate
      neighbor IPV4-UNDERLAY-PEERS activate
      neighbor MLAG-IPV4-UNDERLAY-PEER activate
   !
   vrf A
      rd 10.1.0.117:50001
      route-target import evpn 50001:50001
      route-target export evpn 50001:50001
      router-id 10.1.0.117
      update wait-install
      neighbor 192.2.2.228 peer group MLAG-IPV4-UNDERLAY-PEER
      neighbor 192.2.2.228 description s2-leaf3_Vlan4001
      redistribute connected route-map RM-CONN-2-BGP-VRFS
```

## BFD

### Router BFD

#### Router BFD Multihop Summary

| Interval | Minimum RX | Multiplier |
| -------- | ---------- | ---------- |
| 300 | 300 | 3 |

#### Router BFD Device Configuration

```eos
!
router bfd
   multihop interval 300 min-rx 300 multiplier 3
```

## Multicast

### IP IGMP Snooping

#### IP IGMP Snooping Summary

| IGMP Snooping | Fast Leave | Interface Restart Query | Proxy | Restart Query Interval | Robustness Variable |
| ------------- | ---------- | ----------------------- | ----- | ---------------------- | ------------------- |
| Enabled | - | - | - | - | - |

#### IP IGMP Snooping Device Configuration

```eos
```

## Filters

### Prefix-lists

#### Prefix-lists Summary

##### PL-LOOPBACKS-EVPN-OVERLAY

| Sequence | Action |
| -------- | ------ |
| 10 | permit 10.1.0.0/24 eq 32 |
| 20 | permit 10.1.1.0/24 eq 32 |

##### PL-MLAG-PEER-VRFS

| Sequence | Action |
| -------- | ------ |
| 10 | permit 192.2.2.228/31 |

#### Prefix-lists Device Configuration

```eos
!
ip prefix-list PL-LOOPBACKS-EVPN-OVERLAY
   seq 10 permit 10.1.0.0/24 eq 32
   seq 20 permit 10.1.1.0/24 eq 32
!
ip prefix-list PL-MLAG-PEER-VRFS
   seq 10 permit 192.2.2.228/31
```

### Route-maps

#### Route-maps Summary

##### RM-CONN-2-BGP

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY | - | - | - |

##### RM-CONN-2-BGP-VRFS

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | deny | ip address prefix-list PL-MLAG-PEER-VRFS | - | - | - |
| 20 | permit | - | - | - | - |

##### RM-MLAG-PEER-IN

| Sequence | Type | Match | Set | Sub-Route-Map | Continue |
| -------- | ---- | ----- | --- | ------------- | -------- |
| 10 | permit | - | origin incomplete | - | - |

#### Route-maps Device Configuration

```eos
!
route-map RM-CONN-2-BGP permit 10
   match ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY
!
route-map RM-CONN-2-BGP-VRFS deny 10
   match ip address prefix-list PL-MLAG-PEER-VRFS
!
route-map RM-CONN-2-BGP-VRFS permit 20
!
route-map RM-MLAG-PEER-IN permit 10
   description Make routes learned over MLAG Peer-link less preferred on spines to ensure optimal routing
   set origin incomplete
```

## VRF Instances

### VRF Instances Summary

| VRF Name | IP Routing |
| -------- | ---------- |
| A | enabled |

### VRF Instances Device Configuration

```eos
!
vrf instance A
```
