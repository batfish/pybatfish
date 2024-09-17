# Format of vendor and supplemental data

You can provide two types of data to Batfish: 1) [configurations of devices](#device-configuration-formats) in your network, and 2) [supplemental data](#supplemental-data-formats) to enhance the model of your network. This page describes the format of these data.

## Device configuration formats

Batfish supports the following vendors. Click on the corresponding link to learn how to provide configuration for a specific vendor.

* [A10](#a10)
* [Arista](#arista)
* [AWS](#aws)
* [Cisco](#cisco)
* [Check Point](#check-point)
* [Cumulus Linux](#cumulus-linux)
* [F5 Big IP](#f5-big-ip)
* [Fortinet](#fortinet)
* [Juniper](#juniper)
* [Palo Alto Networks](#palo-alto-networks)
* [SONiC](#sonic)

Except for AWS, all vendor configs files must be placed in the `configs` folder right below the top-level snapshot folder. It is OK to create sub-folders inside `configs`; Batfish will recursively read all files. It is also OK to mix files from multiple vendors in the same folder.

#### Note about vendor detection

Batfish can automatically detect the vendor of a configuration file based on certain tell-tale signs in vendor files. For instance, Arista config files tend to contain lines with "! device: ... EOS-4.24" or "boot system flash ... swi". Such lines are almost always present in config files pulled from devices but may not be present in auto-generated files. 

If you need to explicitly specify the vendor of your configuration file, include the RANCID content type header. So, for Arista devices, you'd include the following line at the top of the file:

`!RANCID-CONTENT-TYPE: arista`

The supported vendor type strings are `arista`, `bigip` (F5), `cisco-nx` (NX-OS), `cisco-xr` (IOS-XR), `force10` (Dell), `foundry`, `juniper` (all JunOS), `mrv`, and `paloalto`.


### A10 

For each A10 device in the network, create a file in the `configs` folder. For v4 and higher versions, the content of the file should be the equivalent of the output of `show running-config partition-config all` command on the device. For v2, use `show running-config all-partitions` command.

### Arista 

For each Arista device in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show running-config` command on the device.

### AWS

Batfish understands AWS VPC configurations and analyzes it just like physical networks.
To use this functionality, place AWS configs in a folder named `aws_configs` right below the top-level snapshot folder.
Each subfolder in this folder should correspond to an AWS account. If you want to analyze only one account, you may skip this level of hierarchy. The subfolders of the account-level folder (or of `aws_configs` if there is only account) correspond to individual regions. If there is only one region,
then this level of hierarchy may be skipped.

The configuration files for a region should be the JSON output of the following API calls:
  * For EC2: `describe_addresses`, `describe_availability_zones`, `describe_customer_gateways`, `describe_instances`, `describe_internet_gateways`, `describe_nat_gateways`, `describe_network_acls`, `describe_network_interfaces`, `describe_prefix_lists`, `describe_route_tables`, `describe_security_groups`, `describe_subnets`, `describe_tags`, `describe_transit_gateway_attachments`, `describe_transit_gateway_route_tables`, `describe_transit_gateway_vpc_attachments`, `describe_transit_gateways`, `describe_vpc_endpoints`, `describe_vpc_peering_connections`, `describe_vpcs`, `describe_vpn_connections`, `describe_vpn_gateways`
  * For ES: `describe_elasticsearch_domains`
  * For RDS: `describe_db_instances`
  * For ELBv2 `describe_listeners`, `describe_load_balancer_attributes`, `describe_load_balancers`, `describe_target_groups`, `describe_target_health`

This output can be collected using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/index.html#cli-aws)
or the [boto3 Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html).
An example script that packages AWS data into a Batfish snapshot is [here](https://github.com/ratulm/bf-aws-snapshot).

An example snapshot, which includes both physical and AWS configs, is [here](https://github.com/batfish/batfish/tree/master/networks/hybrid-cloud-aws).
It is OK to have only AWS configs in a snapshot (without any physical device configs).

### Cisco

Batfish supports Cisco IOS, IOS-XE, IOS-XR, NX-OS, and ASA platforms. For each such device in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show running-config` command on the device.

For NX-OS, we recommend using `show run all` where possible. This output has additional detail that helps with modeling accuracy. 

### Check Point 

Check Point data is provided in two parts.

1. Place the output of `show configuration` from gateway devices into the `configs` folder. This data contains information about interfaces and routing but not firewall policies, which must be fetched from the Check Point Manager as described next.

2. Data from Check Point Manager must be placed in a folder called `checkpoint_management` right under the top-level snapshot folder (parallel to `configs` folder). The expected hierarchy under this folder is as follows:

  * `checkpoint_management`
    * Manager1  [Data from Manager1--you may have multiple managers] 
      * DomainA [Data from DomainA--the manager may have multiple] 
        * show-gateways-and-servers.json
        * show-groups.json
        * show-hosts.json
        * show-networks.json
        * show-package.json
        * show-service-groups.json
        * show-services-icmp.json
        * show-services-other.json
        * show-services-tcp.json
        * show-services-udp.json
        * Package1 [Data for Package1--the domain may have multiple packages] 
          * show-access-rulebase.json  
          * show-nat-rulebase.json     
          * show-package.json 

The json files contain the output of corresponding [Check Point Management API](https://sc1.checkpoint.com/documents/latest/APIs/) calls. 

An example script that fetches this data and organizes it as above is [here](https://github.com/saparikh/bf-checkpoint-manager-snapshot).

### Cumulus Linux

Cumulus devices can be configured by editing individual files, such as `/etc/network/interfaces`, `/etc/cumulus/ports.conf`, and `/etc/frr/frr.conf`
or invoking the [Network Command-Line Utility (NCLU)](https://docs.cumulusnetworks.com/display/DOCS/Network+Command+Line+Utility+-+NCLU)

Batfish supports both the NCLU format and individual Cumulus configuration files. We recommend using the configuration files because Batfish can extract more data from them than from the NCLU output.

```eval_rst
.. note:: If you are using the `BGP Unnumbered` feature on Cumulus devices, you will need to supply `Layer-1 topology`_.
```

#### Cumulus configuration files (recommended)
Batfish processes the Cumulus configuration files concatenated into a single file per device. The format is as follows:

1. hostname (single line)
2. Contents of `/etc/network/interfaces` file
3. Contents of `/etc/cumulus/ports.conf` file
4. Contents of `/etc/frr/frr.conf` file

Batfish detects the boundary between each the concatenated files by looking
for comments or declarations that typically occur at the start of each file.
To ensure they are present for Batfish to find, we recommend adding them in case they are missing.
Here's an example bash snippet:

```bash
hostname=$(cat /etc/hostname)
(
  # hostname
  echo $hostname

  # Signal start of /etc/network/interfaces
  echo "# This file describes the network interfaces"
  cat /etc/network/interfaces
  echo 

  # Signal start of /etc/cumulus/ports.conf
  echo "# ports.conf --"
  cat /etc/cumulus/ports.conf
  echo 

  # Signal start of /etc/frr/frr.conf
  echo "frr version"
  cat /etc/frr/frr.conf
  echo
) > $hostname.cfg
```

Create one concatenated file per device in your network and place the files in the `configs` folder.

#### NCLU output (not recommended)
To retrieve the Cumulus configuration in the NCLU format, issue `net show config commands` and save the output to a file in the `configs` folder.

### F5 BIG-IP

F5 BIG-IP configuration spans multiple individual files, typically the following 3 configuration files:
* Base
* LTM
* Routing [There are 2 formats for this routing configuration. Legacy `imish` and the newer structured format]

These files are typically in a folder named "config" as:
* Base: `bigip_base.conf`
* LTM: `bigip.conf`
* Routing: `bigip_routing.conf`

For Batfish to correctly process the F5 configuration, the 3 files need to be combined into a single file in a specific order.

As an example, let's say you have these 3 files:
* `site1-f5-a-base.conf`
* `site1-f5-a.conf`
* `site1-f5-a-routing.conf`

On any unix machine, simply run:

`cat site1-f5-a-base.conf site1-f5-a.conf site1-f5-a-routing.conf > site1-f5-a-concat.cfg`

Add `site1-f5-a-concat.cfg` to the configs folder with the rest of the devices.

```eval_rst

.. note:: The routing configuration MUST be the last thing copied into the file, otherwise Batfish will not be able to correctly parse the file.
```

### Fortinet 

For each FortiOS firewall, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show` command on the device.

### Juniper

Batfish supports all JunOS-based platforms, including EX, MX, PTX, QFX, SRX, and the T-series. For each such device in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show configuration | display set` command on the device. 

Batfish will also accept JunOS configuration in the hierarchical format and will internally pre-process files in this format to the "set" format.

### Palo Alto Networks
Batfish supports Palo Alto Networks devices with or without Panorama.

#### From Panorama (preferred)
For devices managed through Panorama, with no configuration done directly on the device, you can pull configurations from Panorama without having to run any commands on the managed-devices themselves. If configuration is also done directly on the managed-device, you should follow the instructions for pulling configuration [`From individual devices`](doc:formats#from-individual-devices) instead.

To pull these configurations through Panorama, use the [`pan-python` module](http://api-lab.paloaltonetworks.com/pan-python.html) as follows; note: replace `<IP_ADDR>` and `<LOGIN_USERNAME>` with the IP address and username for the Panorama device:
```text
# Generate an API key and save in .panrc so subsequent commands don't require logging in again
# This only needs to be done once
panxapi.py -t panorama_tag -h <IP_ADDR> -l <LOGIN_USERNAME> -k >> .panrc
# Pull the XML Panorama config
panxapi.py -t panorama_tag -sxr > panorama_config.xml
# Convert the XML Panorama config into set-format
panconf.py --config pan-panorama_config.xml  --set  > panorama_config.set.txt
```
This will generate a single configuration (`panorama_config.set.txt`) representing all firewalls managed by the specified Panorama device, and this config file is what Batfish needs to model the managed firewalls. Place this file in the `configs` folder.

#### From individual devices
For each device, concatenate the following show commands into one file and put the file in the `configs` folder.

```text
set cli config-output-format set
set cli pager off
show config pushed-shared-policy
show config pushed-shared-policy vsys <value> // run for each vsys
show config merged
```

The first two commands may not be available on all PAN-OS versions;
just make sure that the output is NOT in XML format (first command) and that definitions are not truncated (second command).

### SONiC

Configuration files for SONiC devices must be placed under a folder called `sonic_configs` right under the top-level snapshot folder. For each SONiC device in the network, create a folder under the `sonic_configs` folder, and put its files in this folder. Currently, `config_db.json`, `frr.conf`, `resolv.conf`, and `snmp.yml` files are supported. The last two files are optional. File names must end with these respective strings. So, "config_db.json" and "rt123_config_db.json" are valid names for config DB configuration, but "config_db_rt123.json" is not. The device folder must have only these files.

See [this example snapshot](https://github.com/batfish/pybatfish/tree/master/docs/networks/sonic_example) with SONiC configs.

## Supplemental data formats

You can provide additional data to Batfish to enhance the model of your network and to model parts of the network whose configuration is not available. The following types of data is supported.

* [Modeling hosts](#modeling-hosts)
* [Layer-1 topology](#layer-1-topology)
* [Modeling ISPs](#modeling-isps)
* [Runtime interface information](#runtime-interface-information)
* [External BGP announcements](#external-bgp-announcements)

### Modeling hosts

You can model end hosts in the network by adding host files with information about their names, a pointer to their iptables configuration file, and their interfaces. An example host file is:

```
{
  "hostname" : "host1",
  "iptablesFile" : "iptables/host1.iptables",
  "hostInterfaces" : {
    "eth0" : {
      "name": "eth0",
      "prefix" : "2.128.0.101/24"
    }
  }
}
```

`iptables/host1.iptables` is the path relative to the snapshot where this host's iptables configuration can be found. iptables configuration files should be in the format that is generated by `iptables-save`.

There should be one such file per host that you want to model and these files should be placed in a folder called `hosts` right below the top-level snapshot folder. 

See [this example snapshot](https://github.com/batfish/batfish/tree/master/networks/example/live) with host files.

### Layer-1 topology

Batfish can infer Layer-3 interface adjacencies based on IP address configuration on interfaces. For instance, if there are two interfaces in the network with IP assignments `192.168.1.1/24` and `192.168.1.2/24`,
Batfish will infer that these interfaces are adjacent.

Such inference does not work if the network re-uses IP address space or has link-local addresses. In those situations, you must provide a Layer-1 topology file that has cabling information. 
Then, Layer-3 adjacencies will be computed by combining the supplied Layer-1 adjacencies with Layer-2 and Layer-3 configuration to get a more accurate model.

The expected Layer-1 topology file is a JSON file that has a list of edge records, where each edge record has node and interface names of the two ends.
See [this file](https://github.com/batfish/batfish/tree/master/networks/example/example_layer1_topology.json) for an example.

The name of your Layer-1 topology file must be `layer1_topology.json` and it must be placed in a folder called `batfish` right below the top-level snapshot folder.

### Modeling ISPs

Batfish can model ISPs (and Internet connectivity) for a network based on a file that specifies which ISPs to model and how to configure them. The ISP modeling file has a few different sections that control different aspects of the modeling. 

* **BorderInterfaces:** Specify the interfaces in the snapshot that connect to the ISP you want to model. Each interface must be a layer-3 interface connected directly to the ISP and establish an eBGP single-hop session to the ISP. 

```
{
  "borderInterfaces": [
    {
      "borderInterface": {
        "hostname": "as2border1",
        "interface": "GigabitEthernet3/0"
      }
    }, 
    ....
  ]
}
```

* **BgpPeers:** Specify the BGP peers defined on border routers in the snapshot. You can also optionally specify how the ISP attaches to the snapshot, by specifying the interface in the snapshot where it establishes physical connectivity. In the absence of this attachment specification, Batfish will assume that the ISP is attached at the interface of the specified peering.

```
{
  "bgpPeers": [
    {
      "hostname": "as2border1",
      "peerAddress": "10.10.10.10",
      "vrf": "internet",   // Optional; default VRF is assumed if left unspecified
      "ispAttachment": {   // This section is optional. 
          "hostname": "borderSwitch", // Optional; the host of the peering ('as2border1') is assumed if left unspecified
          "interface": "GigabitEthernet3/0",  // mandatory
          "vlanTag": 86 // Specifies the Dot1q encapsulation that the modeled ISP should use for the peering. 
                        // Optional; no tagging is assumed if left unspecified
      }
    }, 
    ....
  ]
}
```

* **Filter:** This section allows you restrict ISPs that are modeled, by specifying the ASNs (`onlyRemoteAsns`) and IPs (`onlyRemoteIps`) of the ISPs. Without this section, all ISPs specified by BorderInterfaces and BgpPeers sections.

```json
{
  "filter": {
    "onlyRemoteAsns": [65432],
    "onlyRemoteIps": ["10.10.10.10"]
  }
}
```

* **IspNodeInfos**: This section lets you configure certain aspects of the modeled ISP nodes. One aspect of this configuration is specifying the role of the ISP---whether it is a transit provider (`TRANSIT`) or a private backbone (`PRIVATE_BACKBONE`) such as a carrier MPLS or your own wide-area network that connects multiple sites. Transit ISPs connects to the modeled Internet node, do not propagate any communities and block reserved address space traffic. Private backbones do not connect to the Internet, propagate (standard and extended) communities and do not filter any traffic.

```
{
  "ispNodeInfo": [
    {
      "asn": 65432,
      "name": "ATT", // Specifies the friendly name (not hostname) to use for the ISP
      "role": "PRIVATE_BACKBONE"  // Optional; default is "TRANSIT"
    },
    ...
   ]
}
```

* **IspPeerings**: This section lets you configure eBGP peering between modeled ISP nodes. When not present, none of the ISPs connect to each other. The specification is:

```
{
   "ispPeerings": [
     {
        "peer1": {
           "asn": 65432,
        },
        "peer2": {
           "asn": 64325,
        }
     },
     ...
   ]
}
```

All sections that you need must be included in a file called `isp_config.json`, placed in a folder called `batfish` right below the top-level snapshot folder. An example snapshot with ISP modeling file is [here](https://github.com/batfish/batfish/tree/master/networks/example/live-with-isp).

The hostname of the modeled ISP nodes will be of the form `isp_<ASN>` (e.g., 'isp_65432'). These nodes can be queried and analyzed just like any other node in the snapshot. Only one node per ASN is generated even if you have multiple peerings to the same ASN.

A node representing the Internet is also created if any of the ISPs is "TRANSIT". This node announces the default route (0.0.0.0/0) to connected ISPs. Its hostname is 'internet' and it too can be queried and analyzed like any other node in the snapshot. 

### Runtime interface information

Batfish infers interface attributes from static configuration files. All relevant information, however, may not be present in the configuration files, including whether an interface is line down and speed/bandwidth for some vendors. You can enhance Batfish's inference of such properties by providing runtime data. 

The format of this data is

```json
{
  "runtimeData": {
    "router1": {
      "Ethernet1/1": {
         "bandwidth": 100000000000,
         "lineUp": false,
         "speed": 100000000000
      }
    },
    "router2": {
      "Ethernet21/1": {
         "lineUp": true
      }
    }    
  }
}
```

The name of this must be `runtime_data.json` and it must be placed in a folder called `batfish` right below the top-level snapshot folder. The same file should contain information for all devices and interfaces, and only a subset of the properties may be specified for an interface. 
 
The runtime data specification also allows you to analyze the impact of failing certain interfaces in the network---just mark them as line down in the data.

### External BGP announcements

To help analyze connectivity to specific external prefixes or analyze the treatment of external routes by your network, you can specify the external routes coming into the network, as follows.

```
{
  "Announcements": [
      {
          "type" : "ebgp_sent", // whether the attributes of this route are what was sent by the external peer, 
                                // or they represent attributes after processing by import routing policy ('ebgp_received')
          "network" : "4.0.0.0/8",
          "nextHopIp" : "10.14.22.4",
          "srcIp" : "10.14.22.4",
          "dstNode" : "as1border2",
          "dstIp" : "10.14.22.1",
          "srcProtocol" : "AGGREGATE",
          "originType" : "egp",
          "localPreference" : 0,
          "med" : 20,
          "originatorIp" : "0.0.0.0",
          "asPath" : [ [ 1239 ], [7018, 7019]],
          "communities" : [ 262145 ],
          "dstVrf":"default",
          "clusterList":[]
      },
      ...
   ]
}
``` 

These announcements must be placed in the file called `external_bgp_announcements.json` and placed inside the top-level snapshot folder. 
