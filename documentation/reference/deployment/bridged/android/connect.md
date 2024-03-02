# Connect a Bridged Android Devive

Connecting a bridged android device starts the VPN connection 

## syntax

```
rib deployment <mode> bridged android connect <args>
```

## Example

```
rib:2.0.0@code# rib deployment local bridged android connect --name=example-deployment
Connecting Android device emulator-5554
Waiting for 1 nodes to connect........done
Connected Android device emulator-5554
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

