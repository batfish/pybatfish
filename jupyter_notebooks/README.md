This folder contains Jupyter notebooks that show how to use Batfish for different analysis and validation tasks. All network snapshots used in the notebooks are in the `networks` subfolder.

The current list of notebooks are:
- **Basics**
    - [Getting Started with Batfish](Getting%20started%20with%20Batfish.ipynb) [[video](https://www.youtube.com/watch?v=Ca7kPAtfFqo)] shows how to get started and provides an overview of the capabilities of Batfish.
    - [Pandas Examples](Pandas%20Examples.ipynb) shows common examples of using Pandas to manipulate Batfish answers.
    - [Validating Configuration Settings](Validating%20Configuration%20Settings.ipynb) [[video](https://www.youtube.com/watch?v=qOXRaVs1Uz4)] shows how to validate different types of configuration settings (NTP server, TACACS server, AAA, SNMP, etc...) using Batfish.
    - [Uncovering Configuration and Behavior Drift](Uncovering%20Configuration%20and%20Behavior%20Drift.ipynb) shows how to analyze conffiguration settings and network behavior differences between two network snapshots.
- **ACLs and firewalls**
    - [Analyzing ACLs and Firewall Rules](Analyzing%20ACLs%20and%20Firewall%20Rules.ipynb) [[video](https://youtu.be/KixQYEDh33s)] shows how to analyze ACLs and firewalls rules using Batfish.
    - [Provably Safe ACL and Firewall Changes](Provably%20Safe%20ACL%20and%20Firewall%20Changes.ipynb) [[video](https://www.youtube.com/watch?v=MJYLVL9UOWk)] shows a workflow to ensure changes to ACLs and firewall rules are correct and safe.
    - [Safely refactoring ACLs and firewall rules](Safely%20refactoring%20ACLs%20and%20firewall%20rules.ipynb) shows how to fully understand the impact of refactoring complex ACLs and firewalls rules.
- **Cloud networking**
   - [Analyzing public and hybrid cloud networks](Analyzing%20public%20and%20hybrid%20cloud%20networks%20.ipynb) shows to analyze cloud and hybrid networks using Batfish.
- **Forwarding analysis**
    - [Introduction to Forwarding Analysis](Introduction%20to%20Forwarding%20Analysis.ipynb) [[video](https://youtu.be/yaJBH3ZZ5Dw)] shows how forwarding paths can be analyzed using traceroute and reachability queries.
    - [Introduction to Forwarding Change Validation](Introduction%20to%20Forwarding%20Change%20Validation.ipynb) [[video](https://youtu.be/Yje70Q8R79w)] shows a workflow to ensure that changes to the network do not impact packet forwarding.
- **Failure-impact analysis**
    - [Analyzing the Impact of Failures (and letting loose a Chaos Monkey)](Analyzing%20the%20Impact%20of%20Failures%20(and%20letting%20loose%20a%20Chaos%20Monkey).ipynb) [[video](https://youtu.be/1adAT6FK-UI)] shows how to analyze the impact of failures on the network and conduct Chaos Monkey style testing.
- **Routing analysis**
    - [Introduction to Route Analysis](Introduction%20to%20Route%20Analysis.ipynb) [[video](https://www.youtube.com/watch?v=AutkFa0xUxg)] shows how to analyze routing tables computed by Batfish.
    - [Introduction to BGP Analysis](Introduction%20to%20BGP%20Analysis.ipynb) shows how to analyze BGP session configuration.
    - [Analyzing Routing Policies](Analyzing%20Routing%20Policies.ipynb) shows how to analyze routing policies using Batfish.

We will continue adding notebooks that demonstrating additional use cases of Batfish.

------

 - You can reach us via [Slack](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTUxOTJlY2YyNTVlNGQ3MTJkOTIwZTU2YjY3YzRjZWFiYzE4ODE5ODZiNjA4NGI5NTJhZmU2ZTllOTMwZDhjMzA) for any questions or suggestions for additional use cases.

 - You can subscribe to the [Batfish YouTube channel](https://www.youtube.com/channel/UCA-OUW_3IOt9U_s60KvmJYA) to be notified of new videos.
