# Down a Deployment

Down'ing a deployment means stopping:
- External Services
    - RiB required services
    - Comms Channel External Services
    - Artifact Manager Plugin External Services
- RACE Nodes

## syntax

```
rib deployment <mode> down <args>
```

## Example

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

## required args

#### --name TEXT
The name of the deployment to down


## optional args

#### --force
Force down removes all containers regardless of node status

#### --node TEXT
Name of inidividual RACE node(s) to down. Defaults to all nodes in Up state. Supports regular expressions.

#### --timeout INTEGER
*Default: 300*
Time to wait for deployment to succesfully down before declaring and error.

####-V, --verbosity
Increase the verbosity of the output

