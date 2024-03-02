# Tar Configs

Tar Configs:
- Creates tar files for each node's configs 

## syntax

```
rib deployment <mode> config tar
```

## example

```
1) rib:x.y.z@code# rib deployment local config tar --name=example-deployment
```

## required args

#### --name TEXT

Name of the deployment to execute this action on

## optional args

#### --node
Name of inidividual RACE node(s) to execute this action on. Defaults to all nodes if not specified. Supports regular expressions.

#### --overwrite
Overwrite existing tar files

#### --timeout INTEGER

*Default: 300*

Number of seconds to allow this action to execute before timing out


