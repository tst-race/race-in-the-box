# Rotate RACE Logs

Rotating RACE logs captures all log files on RACE nodes in a deployment
and places them in the
`~/.race/rib/deployments/<mode>/<deployment_name>/previous-run-logs/<backup_id>/`
directory, then deletes all log files on RACE nodes.

***NOTE*** Capturing logs from an AWS deployment will incur an egress charge
to download the logs from AWS to the local machine. If the log files are very
large, it may be better to SSH into the deployment and view the logs there.

## syntax

```
rib deployment <mode> logs rotate <args>
```

## example

```
1) rib:x.y.z@code# rib deployment local logs rotate --name=example-deployment
Using backup ID: 20220120T192608UTC
Rotating Log Files
Rotated Log Files
1) rib:x.y.z@code# ls ~/.race/rib/deployments/local/example-deployment/previous-run-logs/20220120T192608UTC/
race-client-00001
race-client-00002
race-client-00003
race-server-00001
race-server-00002
race-server-00003
```

## required args

#### `--name TEXT`

Name of the deployment for which to rotate logs.

## optional args

#### `--node TEXT`

Name of individual RACE node(s) for which to rotate logs. Defaults to all nodes
if not specified.

#### `--backup-id TEXT`

Name of the folder under `previous-run-logs` in which to place all captured
logs. Defaults to the current time.

#### `--timeout INTEGER`

*Default: 120*

Number of seconds to allow for log rotation to complete before timing out.

#### `--force`

By default, the log rotate command will fail if the RACE app on the selected
nodes are still running. Setting this switch will force the log rotation to
occur.

