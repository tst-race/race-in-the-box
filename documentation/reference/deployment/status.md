# Report Status For a Deployment

This command is a shortcut for running the following individual status commands:
* [status deployment apps](status/app.md)
* [status deployment containers](status/containers.md)
* [status deployment services](status/services.md)

## syntax

```
rib deployment <mode> status <args>
```

## example

```
1) rib:x.y.z@code# rib deployment local status --name=example-deployment
Deployment example-deployment apps are started
Deployment example-deployment container status is all running
Deployment example-deployment services status is all running
```
