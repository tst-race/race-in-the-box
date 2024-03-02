# Open-Network-Manager-Bypass-Recv

Open a temporary network-manager-bypass receive connection on a given node and, optionally, a given channel, link, or connection.

For more information see this [wiki doc](https://wiki.race.twosixlabs.com/display/RACE2/TA1-bypass+Replacing+TA2-test-mode).

## syntax

```
rib deployment <mode> message open-network-manager-bypass-recv <args>
```

## Example

```
rib:2.0.0@code# rib deployment local message open-network-manager-bypass-recv --name=example-deployment --sender=race-client-00001 --recipient=race-client-00002
Opening network-manager-bypass Receive Connection
Will open network-manager-bypass receive connection the following nodes:
	race-client-00002
rib:2.0.0@code#
```

## required args

#### `--name TEXT`

The name of the deployment

#### `--recipient TEXT`

Which node to open network-manager-bypass receive connection

#### `--sender TEXT`

The node that will be sending to the new receive connection

## optional args

#### `--network-manager-bypass TEXT`

Channel ID, link ID, or connection ID on which to send messages bypassing the
network manager plugin (use '*' for any available channel)
