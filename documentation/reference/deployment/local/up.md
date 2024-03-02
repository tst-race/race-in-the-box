# Up a Deployment

Up'ing a deployment means starting:
- External Services
    - RiB required services
    - Comms Channel External Services
    - Artifact Manager Plugin External Services
- RACE Nodes
    - RiB Daemon runs on each node

## syntax

```
rib deployment <mode> up <args>
```

## Example

```
rib:2.0.0@code# rib deployment local up --name=example-deployment
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

## required args

#### --name TEXT
The name of the deployment to up


## optional args

#### --force
Force up tries to up containers again, regardless of deployment status

#### --node TEXT
Name of inidividual RACE node(s) to stand up. Defaults to all nodes if not specified. Supports regular expressions.

#### --no-publish
Do not publish config tar files to the file server after upping the containers

#### --timeout INTEGER
*Default: 300*
Time to wait for deployment to succesfully Up before declaring and error.

#### -V, --verbosity
Increase the verbosity of the output

