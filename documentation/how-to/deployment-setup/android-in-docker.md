# Android in Docker Deployment Setup

Android in Docker Deployments differ from standard deployments in the following ways:
- Some client containers are linux containers running an Android emulator within it. The emulator can be x86_64 or arm64-v8a
- Not all plugins or channels support Android
- Config Generation may differ

This document only goes over the difference that are important when creating an Android deployment. Plese view the documentation for creating a stardard [local deployment](./local-deployments.md) or [aws deployment](./aws-deployments.md) before proceeding

## Check that Android in Docker is supported

Android in Docker requires the host machine to have `/dev/kvm/` support. This means Mac OS and Windows are not supported. To check if your Linux machine supports Android in Docker you may run the following command:

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
      is_supported: false
      reason: GPU deployments require drivers installed on a Linux host machine
  is_supported: true

```

More information on rib capabilities can be found [here](../../reference/env/local/capabilities.md)

## Choose Node Count
For Android in Docker deployments select >=1 for `--android-client-count`. Android clients will be clients 1 through the selected number of android clients.

## Create the Deployment
```
rib:x.y.z@code# rib deployment local create --name=example-deployment --linux-client-count=2 --linux-server-count=3 --android-client-count=1
Creating New Deployment: example-deployment
Network manager config gen status: complete, reason: success
Created New Deployment: example-deployment
rib:x.y.z@code#
```

More information on the create command can be found here[here](../../reference/deployment/local/create)