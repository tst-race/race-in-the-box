# Prepare a Bridged Android Devive

Preparing a bridged Android device copies required artifacts and configs from the deployment to the bridged device. If the bridged device is also a bootstrapped node, only artifacts for the RACE node daemon will be copied.

## syntax

```
rib deployment <mode> bridged android prepare <args>
```

## Example

```
rib:2.0.0@code# rib deployment local bridged android prepare --name=example-deployment --persona=race-client-00004
```

## required args

#### `--name TEXT`
The name of the deployment.

#### `--persona TEXT`
The persona the bridged device will be. The bridged clients start from the end of the list of clients. (If linux-client-count=2, android-client-count=3 and android-client-bridge-count=2 then race-client-00004 and race-client-00005 are the android bridge clients).

## optional args

#### `--serial TEXT`
Android device serial number. If you only have one device RiB will use it by default. If you have multiple devices use the `adb devices` command to list their serial numbers.

#### `--timeout INTEGER`
Timeout for operation in the range of 0 to 3600 seconds. Defaults to 120 seconds.

#### `-v`
Increase the verbosity of the output.

