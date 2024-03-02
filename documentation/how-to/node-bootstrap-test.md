# Node Bootstrap Test

This document will walk through running a node bootstrap test on a deployment
with nodes that do not have the RACE app already installed or configured.

## Steps

* [Create the Deployment](#create-the-deployment)
* [Stand Up the Deployment](#stand-up-the-deployment)
* [Start the Deployment](#start-the-deployment)
* [Bootstrap the Node](#bootstrap-the-node)
* [Verify Bootstrap Node Is Started](#verify-bootstrapped-node-is-started)
* [Send Messages](#send-messages)
* [Stop the Deployment](#stop-the-deployment)]
* [Tear Down the Deployment](#tear-down-the-deployment)

## Create the Deployment

Create a deployment with the desired network size and plugin revisions. In order
to test the bootstrapping of a node into the RACE network, the deployment must
have at least one "uninstalled", or non-genesis node defined. This is specified
using one of the following flags:

* `--android-client-uninstalled-count`
* `--linux-client-uninstalled-count`
* `--linux-server-uninstalled-count`

These counts are a subset of the total counts for each type. When RiB creates
personas, the genesis (RACE pre-installed) nodes come first followed by the
non-genesis (uninstalled) nodes.

For example, given the options
`--linux-client-count=3 --linux-client-uninstalled-count=2`, client node
`race-client-00001` will be a genesis node and nodes `race-client-00002` and
`race-client-00003` will be non-genesis nodes that can be bootstrapped.

In order to bootstrap, at least one genesis node must also exist to use as the
introducer node. This node is responsible for providing the RACE app and plugin
artifacts to the bootstrapped node, as well as introducing the new node to the
RACE network.

***NOTE*** A bootstrap comms channel must also be included in the deployment in
order for the introducer and target nodes to directly communicate and share
RACE artifacts, configs, and keys. The `twoSixBootstrapCpp` channel is provided
by the Two Six exemplar for testing of bootstrap operations.

```
1) rib:x.y.z@code# rib deployment local create --name=example-deployment \
    --linux-client-count=3 \
    --linux-client-uninstalled-count=1 \
    --linux-server-count=3 \
    --comms-channel=twoSixDirectCpp \
    --comms-channel=twoSixIndirectCpp \
    --comms-channel=twoSixBootstrapCpp
Creating New Deployment: example-deployment
Created New Deployment: example-deployment
```

*See the [deployment setup](./deployment-setup/) guides for additional details.*

## Stand Up the Deployment

Stand up the deployment to start all RACE node containers.

```
1) rib:x.y.z@code# rib deployment local up --name=example-deployment
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
Waiting for 6 nodes to stand up............done
Stood Up Deployment: example-deployment
```

The non-genesis node containers will be started, but their app status will be
`uninstalled` rather than `installed`. This is because they do not have the RACE
app (or any plugins or configs) installed.

```
1) rib:x.y.z@code# rib deployment local status --name=example-deployment -dd
Deployment example-deployment apps are up
	race-client-00001: up
		app: installed
		daemon: started
	race-client-00002: up
		app: installed
		daemon: started
	race-client-00003: up
		app: uninstalled
		daemon: started
	race-server-00001: up
		app: installed
		daemon: started
	race-server-00002: up
		app: installed
		daemon: started
	race-server-00003: up
		app: installed
		daemon: started
Deployment example-deployment container status is healthy
	race-client-00001: healthy
	race-client-00002: healthy
	race-client-00003: healthy
	race-server-00001: healthy
	race-server-00002: healthy
	race-server-00003: healthy
Deployment example-deployment services status is healthy
	ArtifactManager (PluginArtifactManagerTwoSixCpp): running
	RiB Services: healthy
		elasticsearch: healthy
		jaeger-collector: healthy
		jaeger-query: healthy
		kibana: healthy
		rib-file-server: healthy
		rib-redis: healthy
	Comms (twoSixIndirectCpp): running
```

## Start the Deployment

Start the RACE app on all genesis nodes in the deployment. The RACE app on the
non-genesis nodes will not be started, because the app is not installed.

```
1) rib:x.y.z@code# rib deployment local start --name=example-deployment
Starting All Nodes In Deployment: example-deployment (local)
Creating configs archive
Will start the following nodes:
	race-client-00001
	race-client-00002
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 5 nodes to start...done
Started All Nodes In Deployment: example-deployment (local)
```

*See the [`rib deployment start`](../reference/deployment/start.md) reference
for additional details.*

## Bootstrap the Node

Bootstrap the non-genesis node into the RACE network. If an incompatible
combination of introducer and target node is specified, RiB will not continue.

```
1) rib:x.y.z@code# rib deployment local bootstrap node \
    --name=example-deployment \
    --introducer=race-client-00001 \
    --target=race-client-00003
Using randomly generated passphrase: EenOUOuAgkAnHXRnhGwe
Bootstrapping non-RACE Node Into RACE Network
Will bootstrap via the following nodes:
	race-client-00001

Will bootstrap the following nodes:
	race-client-00003

Waiting for 1 nodes to start......done
Bootstrapped Node Into RACE Network
```

*See the
[`rib deployment bootstrap node`](../reference/deployment/bootstrap/node.md)
reference for additional details.*

## Verify Bootstrap Node Is Started

Check the status of the deployment to ensure that the bootstrapped node is now
reporting that the RACE app is running.

```
1) rib:x.y.z@code# rib deployment local status --name=example-deployment -dd
Deployment example-deployment apps are started
	race-client-00001: started
		app: started
		daemon: started
	race-client-00002: started
		app: started
		daemon: started
	race-client-00003: started
		app: started
		daemon: started
	race-server-00001: started
		app: started
		daemon: started
	race-server-00002: started
		app: started
		daemon: started
	race-server-00003: started
		app: started
		daemon: started
Deployment example-deployment container status is healthy
	race-client-00001: healthy
	race-client-00002: healthy
	race-client-00003: healthy
	race-server-00001: healthy
	race-server-00002: healthy
	race-server-00003: healthy
Deployment example-deployment services status is healthy
	ArtifactManager (PluginArtifactManagerTwoSixCpp): running
	RiB Services: healthy
		elasticsearch: healthy
		jaeger-collector: healthy
		jaeger-query: healthy
		kibana: healthy
		rib-file-server: healthy
		rib-redis: healthy
	Comms (twoSixIndirectCpp): running
```

## Send Messages

The bootstrapped node is now ready to send and receive messages.

```
1) rib:x.y.z@code# rib deployment local message send-manual --name=example-deployment \
	--sender=race-client-00002 \
	--recipient=race-client-00003 \
	--message="genesis to bootstrap"
Sending Messages
Will send messages from the following nodes:
	race-client-00002

Sent Messages To Deployment Nodes
```

*See the [`rib deployment message`](../reference/deployment/message/) references
for additional details.*

## Stop the Deployment

```
1) rib:x.y.z@code# rib deployment local stop --name=example-deployment
Stopping All Nodes In Deployment: example-deployment (local)
Will stop the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to stop....done
Stopped All Nodes In Deployment: example-deployment (local)
```

*See the [`rib deployment stop`](../reference/deployment/stop.md) reference for
additional details.*

## Tear Down the Deployment

```
1) rib:x.y.z@code# rib deployment local down --name=example-deployment
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

*See the [`rib deployment local down`](../reference/deployment/local/down.md)
reference for additional details.*
