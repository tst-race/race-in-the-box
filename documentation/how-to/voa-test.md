# VoA Support

The Voice of the Adversary (VoA) capability enables adversary actions to be performed at the SDK level. VoA processing can be configured either through a global configuration file, whose location can be statically configured in the `race.json` file, or dynamically through RiB. This document will walk you through the basic steps of invoking  VoA operations through RiB. Additional information on the VoA functionality, including the format of the global configuration file, and documentation for the various RiB commands can be found at:

https://wiki.race.twosixlabs.com/display/RACE2/Active+and+Passive+VoA+Support

## Steps

* [Pre-requisites](#pre-requisites)
* [Activate VoA processing](#activate-voa-processing)
* [Add a VoA drop rule](#add-a-voa-drop-rule)
* [Add a VoA delay rule](#add-a-voa-delay-rule)
* [Delete all rules](#delete-all-rules)
* [Cleanup](#cleanup)


## Pre-requisites

### Create a deployment

It is assumed that a local RACE deployment named `example-deployment` has already been created with three server nodes and three client nodes. Please see [local-deployments](./deployment-setup/local-deployments.md) for instructions or [deployment-setup](./deployment-setup) for different deployment configuration options.


### Enable VoA support

VoA processing can be enabled or disabled through the `isVoaEnabled` parameter in the `race.json` configuration file. Ensure that this parameter, if defined, is set to `"true"`. VoA processing is enabled by default.

```
1) rib:x.y.z@code# vi ~/.race/rib/deployments/local/example-deployment/configs/global/linux/race.json
1) rib:x.y.z@code# vi ~/.race/rib/deployments/local/example-deployment/configs/global/android/race.json
```

### Up the deployment

```
1) rib:x.y.z@code# rib deployment local up --name example-deployment
Using default RiB mode: local
Using default verbosity: 0
Standing Up Deployment: example-deployment
Will stand up the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Comms (twoSixIndirectCpp) Start External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Start External Services
Waiting for 6 nodes to stand up.....done
Stood Up Deployment: example-deployment
```

### Start the deployment


```
1) rib:x.y.z@code# rib deployment local start --name=example-deployment
Starting All Nodes In Deployment: example-deployment (local)
Creating configs archive
Will start the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to start...done
Started All Nodes In Deployment: example-deployment (local)
```


## Activate VoA processing

Activate VoA processing on all nodes using the following command:

```
1) rib:x.y.z@code# rib deployment local voa activate --name example-deployment
Will set the VoA activation state on the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003
```

## Add a VoA drop rule

Add a rule on race-client-00001 to drop all outgoing packages to `race-server-00003`

```
1) rib:x.y.z@code#  rib deployment local voa add drop --node race-client-00001 --match-type persona --match-value race-server-00003 --rule-id 001 --name example-deployment
Will add VoA rule on the following nodes:
	race-client-00001
```


Verify the drop action by sending a message from `race-client-00001` to `race-client-00002`.


```
1) rib:x.y.z@code#  rib deployment local message send-manual --sender race-client-00001 --recipient race-client-00002 --name example-deployment --message "Hello"
Sending Messages
Will send messages from the following nodes:
	race-client-00001

Sent Messages To Deployment Nodes
```


Observe within the Opentracing logs that the VoA action was applied to packages sent by race-client-00001 to race-server-00003 (see https://wiki.race.twosixlabs.com/display/RACE2/Active+and+Passive+VoA+Support for additional details).

## Add a VoA delay rule

Delete the rule and replace with a 1 second delay action

```
1) rib:x.y.z@code#  rib deployment local voa delete --node race-client-00001 --rule-id 001 --name example-deployment
Will delete VoA rule(s) on the following nodes:
	race-client-00001

1) rib:x.y.z@code#  rib deployment local voa add delay --node race-client-00001 --match-type persona --match-value race-server-00003 --hold-time 1.0 --rule-id 001 --name example-deployment
Will add VoA rule on the following nodes:
	race-client-00001

```

Verify delay action by sending a message from `race-client-00001` to `race-client-00002`.


```
1) rib:x.y.z@code#  rib deployment local message send-manual --sender race-client-00001 --recipient race-client-00002 --name example-deployment --message "Hello again"
Sending Messages
Will send messages from the following nodes:
	race-client-00001

Sent Messages To Deployment Nodes
```

Observe within the Opentracing logs that the VoA action was applied to packages sent by race-client-00001 to race-server-00003 (see https://wiki.race.twosixlabs.com/display/RACE2/Active+and+Passive+VoA+Support for additional details).


## Delete all rules

```
1) rib:x.y.z@code#  rib deployment local voa delete --all --name example-deployment
Will delete VoA rule(s) on the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003
```

Verify delay action by sending a message from `race-client-00001` to `race-client-00002`.


```
1) rib:x.y.z@code#  rib deployment local message send-manual --sender race-client-00001 --recipient race-client-00002 --name example-deployment --message "Hello without VoA"
Sending Messages
Will send messages from the following nodes:
	race-client-00001

Sent Messages To Deployment Nodes
```

Confirm through the Opentracing logs that no VoA action was applied.

## Cleanup

### Stop the deployment

```
1) rib:x.y.z@code#  rib deployment local stop --name example-deployment
Stopping All Nodes In Deployment: example-deployment (local)
Will stop the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to stop...done
Stopped All Nodes In Deployment: example-deployment (local)
```

### Down the deployment

```
1) rib:x.y.z@code#  rib deployment local down --name example-deployment
Using default RiB mode: local
Using default verbosity: 0
Tearing Down Deployment: example-deployment
Will tear down the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to tear down...done
Comms (twoSixIndirectCpp) Stop External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Stop External Services
Tore Down Deployment: example-deployment

```

