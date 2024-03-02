# Local Deployment Setup

This document will walk through creating local deployments with different plugins/configurations. For more information about how to test specific features, please see the other documents under [how-to](../../how-to). For more information about specific commands and their options, please see the documentation under [reference](../../reference)

A **Deployment** consists of:
 - Plugins
    - artifacts
    - supplemental files (config generation scripts, external services scripts, etc.)
    - configs
 - Information about RACE Nodes
    - How many linux servers, linux clients, android clients
    - What docker images to use
- Docker-Compose

## Choose Plugins
A deployment must have:
- 1 network manager plugin
- 1 or more comms channels
    - Most deployments require at least one direct channel and one indirect channel. This is because client-to-server and server-to-client connections must use indirect channel. Direct channels *usually* have higher bandwith and are used server-to-server connections. You can find more information about comms channels in confluence [here](https://wiki.race.twosixlabs.com/display/RACE2/Channel+Surveys)
- 0 or more artifact manager plugins
    - Artifact manager plugins are required if using `--fetch-plugins-on-start` or when bootstrapping a new node. 

## Choose Node Count
Deployments can have linux-server, linux-clients, and android-clients. There are additional parameters to configure each of those types of nodes. There is more information about args [here](../../reference/deployment/local/create.md) and more information about testing specific features in the other [how-to's](../../how-to).

## Create the Deployment

```
rib deployment local create \
	--name=example-deployment \
	--linux-client-count=3 \
	--linux-server-count=3
```

More information on the create command can be found [here](../../reference/deployment/local/create.md)