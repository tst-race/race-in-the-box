# GPU Deployment Setup

GPU Deployments differ from standard deployments in the following ways:
- Plugins can access the GPU for increased performance

This document only goes over the difference that are important when creating a GPU deployment. Plese view the documentation for creating a stardard [local deployment](./local-deployments.md) or [aws deployment](./aws-deployments.md) before proceeding

## Check that GPU Deployments are supported

GPU Deployments require the host machine to have a GPU, proper drivers installed, and to be Linux. To check if your Linux machine supports GPU Deployments you may run the following command:

```
1) rib:x.y.z@code# rib env local capabilities
Android:
  children:
    Android Bridge Mode:
      is_supported: true
    Android in Docker:
      is_supported: true
  is_supported: true
Local Deployments:
  children:
    GPU Deployments:
      is_supported: true
  is_supported: true

```

More information on rib capabilities can be found [here](../../reference/env/local/capabilities.md)

*Note* As of RiB 2.0.0 the capabilities check is not exhaustive. It does not check for proper drivers. Additional checks may be added in future versions of RiB.

## Create the Deployment

The only difference between a GPU deployment and a standard deployment is the addition of the `--enable-gpu` flag as shown below. 

```
rib:x.y.z@code# rib deployment local create --name=example-deployment --linux-client-count=2 --linux-server-count=3 --enable-gpu
Creating New Deployment: example-deployment
Network manager config gen status: complete, reason: success
Created New Deployment: example-deployment
rib:x.y.z@code#
```

More information on the create command can be found here[here](../../reference/deployment/local/create)