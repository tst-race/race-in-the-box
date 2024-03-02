# Delete RACE Logs

Deleting RACE logs removes all log files on RACE nodes in a deployment.

## syntax

```
rib deployment <mode> logs delete <args>
```

## example

```
1) rib:x.y.z@code# rib deployment local logs delete --name=example-deployment
Deleting Log Files
Deleted Log Files
```

## required args

#### `--name TEXT`

Name of the deployment for which to delete logs.

## optional args

#### `--node TEXT`

Name of individual RACE node(s) for which to delete logs. Defaults to all nodes
if not specified.

#### `--timeout INTEGER`

*Default: 120*

Number of seconds to allow for log deletion to complete before timing out.

#### `--force`

By default, the log delete command will fail if the RACE app on the selected 
nodes are still running. Setting this switch will force the log deletion to
occur.
