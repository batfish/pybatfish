# Format of vendor and supplemental data

## Vendor formats

For vendors whose device configuration is not a single text file,
additional preprocessing may be necessary before uploading data to Batfish.

### AWS

Batfish understands AWS VPC configurations and analyzes it just like physical networks.
To use this functionality, place AWS configs in a top-level folder called `aws_configs`.
The subfolders in this folder correspond to individual regions. If there is only one region,
then this level of hierarchy may be skipped.

The configuration files for a region should be the JSON output of the following API calls:
  * For EC2: `describe_addresses`, `describe_availability_zones`, `describe_customer_gateways`, `describe_internet_gateways`, `describe_network_acls`, `describe_network_interfaces`, `describe_instances`, `describe_route_tables`, `describe_security_groups`, `describe_subnets`, `describe_vpc_endpoints`, `describe_vpcs`, `describe_vpn_connections`, `describe_vpn_gateways`
  * For ES: `describe_elasticsearch_domains`
  * For RDS: `describe_db_instances`

This output can be collected using the [AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/index.html#cli-aws)
or using the [boto3 Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html).

An example script that packages AWS data into a Batfish snapshot is [here](https://github.com/ratulm/bf-aws-snapshot).

An example snapshot, which includes both physical and AWS configs, is [here](https://github.com/batfish/batfish/tree/master/networks/hybrid-cloud-aws).
It is OK to have only AWS configs in a snapshot.

### Cumulus Linux

Cumulus devices can be configured by editing individual files, such as `/etc/network/interfaces`, `/etc/cumulus/ports.conf`, and `/etc/frr/frr.conf`
or invoking the [Network Command-Line Utility (NCLU)](https://docs.cumulusnetworks.com/display/DOCS/Network+Command+Line+Utility+-+NCLU)

Batfish supports processing of either NCLU configuration output,
or the Cumulus configuration files themselves (concatenated into one file per device).
We recommend using the configuration files, because Batfish can extract more data from them than from the NCLU output.

```eval_rst
.. note:: If you are using the `BGP Unnumbered` feature on Cumulus devices, you will need to supply a `Layer-1 topology file`_.
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

#### Cumulus: NCLU output (not preferred)
To retrieve the Cumulus configuration in the NCLU format, issue `net show config commands` and save the output to a file.

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

### Palo Alto Networks
Batfish supports Palo Alto Networks devices with or without Panorama.

#### From Panorama (preferred)
For devices managed through Panorama, with no configuration done directly on the device, you can pull configurations from Panorama without having to run any commands on the managed-devices themselves.

To pull these configurations through Panorama, use the [`pan-python` module](http://api-lab.paloaltonetworks.com/pan-python.html) as follows; note: replace `<IP_ADDR>` and `<LOGIN_USERNAME>` with the IP address and username for the Panorama device:
```
# Generate an API key and save in .panrc so subsequent commands don't require logging in again
# This only needs to be done once
panxapi.py -t panorama_tag -h <IP_ADDR> -l <LOGIN_USERNAME> -k >> .panrc
# Pull the XML Panorama config
panxapi.py -t panorama_tag -sxr > panorama_config.xml
# Conver the XML Panorama config into set-format
panconf.py --config pan-panorama_config.xml  --set  > panorama_config.set.txt
```
This will generate a single configuration (`panorama_config.set.txt`) representing all firewalls managed by the specified Panorama device, and this config file is what Batfish needs to model the managed firewalls.

#### From individual devices
For each device, concatenate the following show commands into one file.

```text
set cli config-output-format set
set cli pager off
show config pushed-shared-policy
show config pushed-shared-policy vsys <value> // run for each vsys
show config merged
```

The first two commands may not be available on all PAN-OS versions;
just make sure that the output is NOT in XML format (first command) and that definitions are not truncated (second command).


## Batfish data formats

### Host JSON files

The host JSON files contain basic information about the hosts attached to the network, including their names, a pointer to their iptables configuration file, and their interfaces. An example file is:

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


### Layer-1 topology file

Normally Batfish infers Layer-3 interface adjacencies based on IP address configuration on interfaces.

For instance, if there are two interfaces in the network with IP assignments `192.168.1.1/24` and `192.128.1.2/24` respectively,
Batfish will infer that these interfaces are adjacent.

However, you may override this behavior by supplying a Layer-1 topology file.
In this case, Layer-3 adjacencies are computed by combining the supplied Layer-1 adjacencies with Layer-2 and Layer-3 configuration to get a more accurate model.
This is especially useful if IP addresses are reused across the network on interfaces that are not actually adjacent in practice.

The expected Layer-1 topology file is a JSON file that has a list of edge records, where each edge record has node and interface names of the two ends.
See [this file](https://github.com/batfish/batfish/tree/master/networks/example/example_layer1_topology.json) for an example.
Your file name should be `layer1_topology.json` for it to be considered by Batfish.


### ISP configuration

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

```eval_rst
.. warning:: Batfish will not try to model any ISP routers in the absence of this configuration file.
```

An example network with ISP modeling configuration is [here](https://github.com/batfish/batfish/tree/master/networks/example/live-with-isp).
