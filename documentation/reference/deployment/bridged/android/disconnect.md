# Unrepare a Bridged Android Devive

Disconnecting a bridged android device stops the VPN connection to the RiB overlay network.

## syntax

```
rib deployment <mode> bridged android disconnect <args>
```

## Example

```
rib:2.0.0@code# rib deployment local bridged android disconnect --name=example-deployment
rib:2.0.0@code#
```

## required args

#### --name TEXT
The name of the deployment


## optional args

#### --serial TEXT
Android device serial number (defaults if there's only one device)

#### --timeout INTEGER
*Default: 120*
Timeout for operation (in seconds) 0<=x<=3600

####-v
Increase the verbosity of the output

