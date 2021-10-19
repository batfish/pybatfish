# Format of vendor and supplemental data

You can provide two types of data to Batfish: 1) configurations of devices in your network, and 2) supplemental data to enhance the model of your network. This page describes the format in these data.

## Vendor configuration formats

Batfish supports the following vendors. Click on the corresponding link to learn how to provide configuration for the vendor.

* [Arista](#arista)
* [AWS](#aws)
* [Cisco](#cisco)
* [Cumulus Linux](#cumulus-linux)
* [F5 Big IP](#f5-big-ip)
* [Fortinet](#fortinet)
* [Juniper](#juniper)
* [Palo Alto Networks](#palo-alto-networks)

Except for AWS, all vendor configs files are placed in the `configs` folder right below the top-level snapshot folder. It is OK to create sub-folders inside `configs` and Batfish will recursively read all files. It is also OK to mix files from different vendors in the same folder.

#### Note about vendor detection

Batfish can automatically detect the vendor of a configuration file based on certain tell-tale signs in vendor files. For instance, Arista config files tend to contain lines with "! device: ... EOS-4.24" or "boot system flash ... swi". Such lines are almost always present in config files pulled from devices but may not be present in auto-generated files. 

If you need to explicitly specify the vendor of your configuration file, include the RANCID content type header. So, for Arista devices, you'd include the following line at the top of the file:

`!RANCID-CONTENT-TYPE: arista`

The supported vendor type strings are `arista`, `bigip` (F5), `cisco-nx` (NX-OS), `cisco-xr` (IOS-XR), `force10` (Dell), `foundry`, `juniper` (all JunOS), `mrv`, and `paloalto`.


### Arista 

For each Arista device in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show running-config` command on the device.

### AWS

Batfish understands AWS VPC configurations and analyzes it just like physical networks.
To use this functionality, place AWS configs in a folder named `aws_configs` right below the top-level snapshot folder.
The subfolders in this folder correspond to individual regions. If there is only one region,
then this level of hierarchy may be skipped.

The configuration files for a region should be the JSON output of the following API calls:
  * For EC2: `describe_addresses`, `describe_availability_zones`, `describe_customer_gateways`, `describe_internet_gateways`, `describe_network_acls`, `describe_network_interfaces`, `describe_instances`, `describe_route_tables`, `describe_security_groups`, `describe_subnets`, `describe_vpc_endpoints`, `describe_vpcs`, `describe_vpn_connections`, `describe_vpn_gateways`
  * For ES: `describe_elasticsearch_domains`
  * For RDS: `describe_db_instances`

This output can be collected using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/index.html#cli-aws)
or the [boto3 Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html).
An example script that packages AWS data into a Batfish snapshot is [here](https://github.com/ratulm/bf-aws-snapshot).

An example snapshot, which includes both physical and AWS configs, is [here](https://github.com/batfish/batfish/tree/master/networks/hybrid-cloud-aws).
It is OK to have only AWS configs in a snapshot (without any physical device configs).

### Cisco

Batfish supports Cisco IOS, IOS-XE, IOS-XR, NX-OS, and ASA platforms. For each such device in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show running-config` command on the device.

For NX-OS, we recommend using `show run all` where possible. This output has additional detail that helps with modeling accuracy. 

### Cumulus Linux

Cumulus devices can be configured by editing individual files, such as `/etc/network/interfaces`, `/etc/cumulus/ports.conf`, and `/etc/frr/frr.conf`
or invoking the [Network Command-Line Utility (NCLU)](https://docs.cumulusnetworks.com/display/DOCS/Network+Command+Line+Utility+-+NCLU)

Batfish supports both the NCLU format and individual Cumulus configuration files. We recommend using the configuration files because Batfish can extract more data from them than from the NCLU output.

```eval_rst
.. note:: If you are using the `BGP Unnumbered` feature on Cumulus devices, you will need to supply `Layer-1 topology`_.
```

#### Cumulus configuration files (preferred)
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

  # Signal start of /etc/cumulus/ports.conf
  echo "# ports.conf --"
  cat /etc/cumulus/ports.conf

  # Signal start of /etc/frr/frr.conf
  echo "frr version"
  cat /etc/frr/frr.conf
) > $hostname.cfg
```

Create one file per device in your network and place the files in the `configs` folder.

#### NCLU output (not preferred)
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

For each FortiOS firewall in the network, create a file in the `configs` folder. The content of the file should be the equivalent of the output of `show` command on the device.

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


## Supplemental data format

You can provide additional data to Batfish to enhance the model of your network or model parts of the network whose configuration is not available. 

### Modeling hosts

The host files enable you to model end hosts in the network by providing information about their names, a pointer to their iptables configuration file, and their interfaces. An example host file is:

```json
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

Batfish can infer Layer-3 interface adjacencies based on IP address configuration on interfaces. For instance, if there are two interfaces in the network with IP assignments `192.168.1.1/24` and `192.128.1.2/24` respectively,
Batfish will infer that these interfaces are adjacent.

However, such inference does not work if you have IP address re-use or are link-local addresses. You can override the inferred connectivity by supplying a Layer-1 topology file that has the cabling information for your network. 
Then, Layer-3 adjacencies will be computed by combining the supplied Layer-1 adjacencies with Layer-2 and Layer-3 configuration to get a more accurate model.

The expected Layer-1 topology file is a JSON file that has a list of edge records, where each edge record has node and interface names of the two ends.
See [this file](https://github.com/batfish/batfish/tree/master/networks/example/example_layer1_topology.json) for an example.

The name of your Layer-1 topology file must be `layer1_topology.json` and it must be placed in a folder called `batfish` right below the top-level snapshot folder.

### Modeling ISPs

Batfish can model routers representing ISPs (and Internet) for a given network.
The modeling is based on a json configuration file (`isp_config.json`),
which tells Batfish about the interfaces on border routers which peer with the ISPs.
An example file is:

```json
{
  "borderInterfaces": [
    {
      "borderInterface": {
        "hostname": "as2border1",
        "interface": "GigabitEthernet3/0"
      }
    }, {
      "borderInterface": {
        "hostname": "as2border2",
        "interface": "GigabitEthernet3/0"
      }
    }
  ],
  "filter": {
    "onlyRemoteAsns": [],
    "onlyRemoteIps": []
  }
}
```

Here `borderInterfaces` contains the list of interfaces on border routers which are meant to peer with the ISPs.
`onlyRemoteAsns` (list of ASNs) and `onlyRemoteIps` (list of IPs) provide a way to apply additional filter by restricting to ISPs having specific ASNs or IPs.

The name of your ISP modeling file must be `isp_config.json` and it must be placed in a folder called `batfish` right below the top-level snapshot folder. An example network with ISP modeling configuration is [here](https://github.com/batfish/batfish/tree/master/networks/example/live-with-isp).

### Runtime interface information

Batfish infers interface state and speed from static configuration files. All relevant information, however, may not be present in the configuration files, including whether an interface is line down and speed/bandwidth for some vendors. You can override Batfish's inference of these properties by providing runtime data. 

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
 

