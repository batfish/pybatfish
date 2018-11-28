**Got questions, feedback, or feature requests? Join our community on [Slack!](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTUxOTJlY2YyNTVlNGQ3MTJkOTIwZTU2YjY3YzRjZWFiYzE4ODE5ODZiNjA4NGI5NTJhZmU2ZTllOTMwZDhjMzA)**

# Pybatfish

Pybatfish is a Python client for [Batfish](https://github.com/batfish/batfish). ![Analytics](https://ga-beacon.appspot.com/UA-100596389-3/open-source/pybatfish?pixel&useReferer)


## What is Batfish?

[![Getting to know Batfish](batfish_video.png)](https://www.youtube.com/watch?v=Ca7kPAtfFqo)

Batfish is a network validation tool that provides correctness guarantees for security, reliability, and compliance by analyzing the configuration of network devices. 

The primary use case for Batfish is to evaluate planned configuration changes in order to understand the impact of the change. Pre-deployment validation is a critical gap in existing network automation workflows. 

While pre-deployment validation is the primary use case, Batfish can also be used to provide post-change validation.

Batfish builds complete models of network behavior from device configurations and finds violations of network policies (built-in, user-defined, and best-practices). By integrating Batfish into their network automation workflow, network engineers can close this gap and ensure that only correct changes are deployed.


**The Batfish service does NOT require direct access to network devices**, as the core analysis just requires the configuration of network devices. Additional information from the network can also be fed into Batfish to enhance the analysis. That information includes, but is not limited to:

* BGP routes received from external peers
* Topology information represented by LLDP/CDP

See [www.batfish.org](http://www.batfish.org) for technical information on how it works. ![Analytics](https://ga-beacon.appspot.com/UA-100596389-3/open-source/batfish?pixel&useReferer)


## What kinds of correctness checks does Batfish support?

Batfish can provide correctness guarantees for a wide range of network behaviors and device configuration attributes, for example:
#### Configuration Compliance
* Flag undefined-but-referenced or defined-but-unreferenced structures (e.g., ACLs, route maps)
* Validate configuration settings for MTUs, AAA, NTP, logging, etc. [[video](https://www.youtube.com/watch?v=qOXRaVs1Uz4)]
* Devices can only be accessed using SSHv2 and password is not null
#### Security and Availability
* ACLs and firewalls block all and only disallowed traffic [[video](https://youtu.be/KixQYEDh33s)]
* Compute and compare the routes learned by each node [[video](https://www.youtube.com/watch?v=AutkFa0xUxg)]
* Smart traceroute and end-to-end reachability validation (e.g., DNS is globally reachable, sensitive services can only be reached from specific subnets) [[video](https://youtu.be/yaJBH3ZZ5Dw)]
#### Change and Failure Analysis
* End-to-end reachability is identical across the current and a planned configuration
* End-to-end reachability is identical in the face of a single-link or single-device failure
* Planned ACL or firewall changes are provably correct and cause no collateral damage for other traffic [[video](https://www.youtube.com/watch?v=MJYLVL9UOWk)]
* Two configurations, potentially from different vendors, are functionally equivalent

  
## How do I get started?

Follow the instructions listed in the [batfish github repository](https://github.com/batfish/batfish/blob/master/README.md)


### Pybatfish documentation

Complete documentation of pybatfish APIs is [here](https://pybatfish.readthedocs.io/en/latest/). 
