# Manual Deployment Test

This document will walk through running a manual deployment test. For more information about how to test specific features, please see the other documents under [how-to](../how-to). For more information about specific commands and their options, please see the documentation under [reference](../reference)


## Create the Deployment
Create your deployment with the specific configuration you want to test. Please see more information on different deployment configuration options in [deployment-setup](./deployment-setup). The most simple example is [local-deployments](./deployment-setup/local-deployments.md)

```
rib deployment local create \
	--name=example-deployment \
	--linux-client-count=3 \
	--linux-server-count=3
```

## Up the Deployment
```
rib:x.y.z@code# rib deployment local up --name=example-deployment
Using default RiB mode: local
Using default verbosity: 1
Standing Up Deployment: example-deployment
Current status:
	0/6 nodes are unknown
	6/6 nodes are down
	0/6 nodes are up
	0/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	8/8 services are down
	0/8 services are up

Will stand up the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Comms (twoSixIndirectCpp) Start External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Start External Services
Waiting for 6 nodes to stand up......done
Current status:
	0/6 nodes are unknown
	0/6 nodes are down
	0/6 nodes are up
	6/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	1/8 services are down
	7/8 services are up
    
Stood Up Deployment: example-deployment
rib:2.0.0@code#
```
More information on the up command can be found [here](../reference/deployment/local/up.md)

## Start the deployment
```
rib:2.0.0@code# rib deployment local start --name=example-deployment
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
rib:2.0.0@code#
```
More information on the start command can be found [here](../reference/deployment/start.md)


## Send messages
There are a number of ways to send messages. For this walkthrough we will send manual messages. More information on the other ways to send messages can be found [here](../reference/deployment/message/)

```
rib:2.0.0@code# rib deployment local message send-manual --name=example-deployment --message=hi
Sending Messages
Will send messages from the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003

Sent Messages To Deployment Nodes
rib:2.0.0@code#
```

### network-manager-bypass

By default, messages are encrypted and routed by the network manager plugin. If
`--network-manager-bypass` is used you can bypass the network manager and send
messages on a single point-to-point connection. This means the sender or
receiver can be a server node.

## Verify message received
There are multiple ways to verify a message was successfully received. For this test we will verify via logs on the node. More information on how to verify messages can be found [here](./test/verification/message-receipt.md)

With a local deployment we can docker exec into the recipient node from a non RiB terminal:
```
mac: user$ docker exec -it race-client-00002 bash
```
Then verify the logs
```
root@race-client-00002:/code# tail /log/racetestapp.log 
2022-01-19 22:26:59: INFO: Received message: checksum: e9aae456c957bbf52c99ce84d893be0f4025174c, size: 12, nonce: 10, from: race-client-00001, to: race-client-00002, test-id: default, sent-time: 1642631212061030, traceid: 3992cbd16848f1cd, recv-time: 1642631219383479, message: default 0002
``` 

## Stop deployment
Now that we have verified a basic message test, we can stop and down our deployment.

```
rib:2.0.0@code# rib deployment local stop --name=example-deployment
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
rib:2.0.0@code#
```

More information on the stop command can be found [here](../reference/deployment/stop.md)
## Down deployment

```
rib:2.0.0@code# rib deployment local down --name=example-deployment
Using default RiB mode: local
Using default verbosity: 1
Tearing Down Deployment: example-deployment
Current status:
	0/6 nodes are unknown
	0/6 nodes are down
	0/6 nodes are up
	6/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	0/8 services are down
	8/8 services are up

Will tear down the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

docker-compose command: docker-compose --file=/root/.race/rib/deployments/local/example-deployment/docker-compose.yml stop
docker-compose command: docker-compose --file=/root/.race/rib/deployments/local/example-deployment/docker-compose.yml rm --force
Waiting for 6 nodes to tear down...done
Current status:
	0/6 nodes are unknown
	6/6 nodes are down
	0/6 nodes are up
	0/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	6/8 services are down
	2/8 services are up

Comms (twoSixIndirectCpp) Stop External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Stop External Services
Network rib-overlay-network is external, skipping
Tore Down Deployment: example-deployment

rib:2.0.0@code#
```

More information on the down command can be found [here](../reference/deployment/local/down.md)