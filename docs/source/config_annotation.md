## Configuration file annotation

Batfish may ignore certain lines, or portions of a line, in your configuration files. Such lines fall in one of these categories:

1. Batfish does not understand the content of the line (unrecognized syntax) 
2. Batfish does not support the feature mentioned in the line
3. Batfish deems that the line is irrelevant to its network model

The first two categories of ignored lines are reported in the [initIssues question](notebooks/snapshot.html#Snapshot-Initialization-Issues); the third category is not. 

If you wanted a full account of what is ignored, we have created a tool that annotates each line in the config file. The annotation is one of the following, respectively, corresponding to the categories above

 1. UNRECOGNIZED SYNTAX
 2. PARTIALLY UNSUPPORTED 
 3. SILENTLY IGNORED

In each case, the annotation is followed by the part of the line to which the annotation applies.
 
Using this tool requires building Batfish from source (i.e., not pre-built Docker images). If you are using Bazel, you can run this tool as

```
bazel run //tools:annotate <input dir> <output dir>
```

It will read all files in the input dir and output an annotated version in the output dir. The annotations mention which lines are being fully or partially ignored by the analysis. No annotation is added for lines that are fully supported. 

Example output for a file:

```
!
! SILENTLY IGNORED: version 15.2
version 15.2
!
hostname as1border1
!
! SILENTLY IGNORED: boot-start-marker
boot-start-marker
! SILENTLY IGNORED: boot-end-marker
boot-end-marker
!
no aaa new-model
! SILENTLY IGNORED: no ip icmp rate-limit unreachable
no ip icmp rate-limit unreachable
! SILENTLY IGNORED: ip cef
ip cef
!
!
no ip domain lookup
ip domain name lab.local
!
...
...
```