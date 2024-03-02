# Artifact Manager Plugin Deployment Setup

Artifact Manager Deployments differ from standard deployments in the following ways:
- Plugin (network manager, comms) artifacts are not volume mounted in the RACE Nodes
- The Artifact Manager Plugin is used to fetch network manager/comms artifacts on `start`

This document only goes over the difference that are important when creating a Artifact Manager deployment. Plese view the documentation for creating a stardard [local deployment](./local-deployments.md) or [aws deployment](./aws-deployments.md) before proceeding


## Create the Deployment

The only difference between a Artifact Manager Plugin deployment and a standard deployment (from a RiB command perspective) is the addition of the `--fetch-plugins-on-start` flag as shown below.

By default the TwoSix Stub is used as the Artifact Manager Plugin.

```
rib:x.y.z@code# rib deployment local create --name=example-deployment --linux-client-count=2 --linux-server-count=3 --fetch-plugins-on-start
Creating New Deployment: example-deployment
Network manager config gen status: complete, reason: success
Created New Deployment: example-deployment
rib:x.y.z@code#
```

More information on the create command can be found here[here](../../reference/deployment/local/create)