# Start a Deployment

Starting a deployment means starting the RACE app on all specified nodes

## syntax

```
rib deployment <mode> start <args>
```

## Example

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

## required args

#### --name TEXT
The name of the deployment to start


## optional args

#### --force
Force up tries to up containers again, regardless of deployment status

#### --node TEXT
Name of inidividual RACE node(s) to start. Defaults to all nodes if not specified. Supports regular expressions.

#### --timeout INTEGER
*Default: 300*
Time to wait for deployment to succesfully start before declaring and error.

####-V, --verbosity
Increase the verbosity of the output

