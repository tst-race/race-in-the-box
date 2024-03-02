# Bootstrap a Node

Bootstrapping introduces a non-RACE node into the RACE network

## syntax

```
rib deployment <mode> bootstrap node <args>
```

## example

```
1) rib:x.y.z@code# rib deployment local bootstrap node \
    --introducer race-client-00001
    --target race-client-00002
```

## required args

#### `--name TEXT`

Name of the deployment in which to bootstrap a node.

#### `--introducer TEXT`

Name of the node to act as the introducer for the bootstrapped node. This node
will be responsible for preparing the RACE artifacts and configs in order to
install RACE on the target node. It will also be responsible for introducing
the new node to the RACE network.

#### `--target TEXT`

Name of the non-RACE node to be bootstrapped.

## optional args

#### `--passphrase TEXT`

*Default: random string*

Passphrase to use between the introducer and target nodes.

#### `--force`

By default, the bootstrap command will fail if the introducer and target nodes
are not supported combinations. Setting this switch will force the bootstrap
operation to continue.
