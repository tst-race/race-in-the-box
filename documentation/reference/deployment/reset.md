# Reset Nodes

Reset Nodes:
- Triggers the daemon action to rest each node
- Deletes runtime configs and configs tar files
- Redownloads configs
- Uninstalls RACE if the node was a bootstrap node

## syntax

```
rib deployment <mode> reset
```

## example

```
1) rib:x.y.z@code# rib deployment local reset --name=example-deployment
```

## required args

#### --name TEXT

Name of the deployment to execute this action on

## optional args

#### --node
Name of inidividual RACE node(s) to execute this action on. Defaults to all nodes if not specified. Supports regular expressions.

#### --force
Ignore precondition status checks

#### --timeout INTEGER

*Default: 300*

Number of seconds to allow this action to execute before timing out


