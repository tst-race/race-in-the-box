# Android Bridged Deployment Setup

Android Bridged Deployments differ from standard deployments in the following ways:
- Android App runs on a standalone emulator or physical phone

This allows for testing on real phones or for android testing on machines that don't support Android in Docker. This document only goes over the difference that are important when creating an Android Bridged deployment. Plese view the documentation for creating a stardard [local deployment](./local-deployments.md) or [aws deployment](./aws-deployments.md) before proceeding

## Check that Android Bridged Deployments are supported

Android Bridged Deployments require the host machine to have a [ADB](https://developer.android.com/studio/command-line/adb) installed. After installing ADB, check if your machine supports Android Bridged Deployments by running the following command:

```
1) rib:x.y.z@code# rib env local capabilities
Android:
  children:
    Android Bridge Mode:
      is_supported: true
    Android in Docker:
      is_supported: true
  is_supported: true
Local Deployments:
  children:
    GPU Deployments:
      is_supported: true
  is_supported: true

```

More information on rib capabilities can be found [here](../../reference/env/local/capabilities.md)

> :information_source: As of RiB 2.0.0 the capabilities check is not exhaustive. It does not check for proper drivers. Additional checks may be added in future versions of RiB.

## Device (Physical Phone/Emulator) Setup

The RACE App currently supports Android API 29 on x86_64 or arm64 architectures. Please make sure your device meets these requirements and note the architecture which will be required shortly.

In addition to those requirements, the device also requires `OpenVPN for Android`(supported on x86_64) or OpenVPN Connect (supported on arm64).

If you have multiple devicess you will need to note the device id using `adb get-serialno`. Once your device is running/connected you are ready to continue.

## Create the Deployment

When creating an Android Bridged Deployment specificy `--android-client-count` and `--android-client-bridge-count`. android-client-bridge-count is a subset of android-client-count.

```
rib:x.y.z@code# rib deployment local create \
	--name=example-bridged-deployment \
  --race-core local=/code/race-core/kits \
	--linux-client-count=2 \
	--linux-server-count=3 \
	--android-client-count=1 \
	--android-client-bridge-count=1
Creating New Deployment: example-deployment
Network manager config gen status: complete, reason: success
Created New Deployment: example-deployment
rib:x.y.z@code#
```

More information on the create command can be found here[here](../../reference/deployment/local/create)

## Prepare Bridged Device

The deployment contains the RACE apk, plugin artifacts, configs, and ovpn token, all of which are required for the bridged device to connect to the RACE network. There is a RiB command that must be run for each deployment prior to connecting the bridged device.

The ovpn token is used to configure OpenVPN or OpenVPN Connect. Information about installing VPN Client can be found [here](../../general/Prerequisites.md)

If you have a single device then RiB commands will use it by default. If you have multiple devices you will need the serial number of the Android device. To get it run the `adb devices` command on your host machine.

```bash
$ adb devices
List of devices attached
ABCD0123456789  device
```

> :information_source: When starting RiB, the entrypoint script ([rib.sh](../../../docker-image/rib.sh)) attempts to get the correct IP address to use for the VPN. If the configured IP address is incorrect, you can set it manually with an argument to the RiB entrypoint script.

> :information_source: The bridged clients start from the end of the list of clients. (If `linux-client-count=2`, `android-client-count=3` and `android-client-bridge-count=2` then `race-client-00004` and `race-client-00005` are the android bridge clients)

```
rib:x.y.z@code# rib deployment local bridged android prepare --name=example-bridged-deployment --persona=race-client-00004

# If you have multiple devices and need to specify which to prepare.
rib:x.y.z@code# rib deployment local bridged android prepare --name=example-bridged-deployment --persona=race-client-00004 --serial=ABCD0123456789
```

### Pushing Configs as Part of Prepare

Optionally, you can push configs to your device in the call to `prepare` by providing the `--push-configs` flag. Normally configs are pulled from the RiB file server to the device during the `connect` command. By pushing configs to the device during `prepare` you can emulate the case of a real-world device which would not have access to RiB range services.

Note that if you push configs during `prepare` you must also:
1. Skip calling the `connect` command (described in the section [Connect Bridged Device](connect-bridged-device)).
1. Manually connect to the deployment VPN by opening the `OpenVPN Connect` app on your device and connecting the race profile.

### Running Without the RACE Node Daemon

You can optionally choose to not install the RACE node daemon for more complete testing/emulation of real-world scenarios using physical devices. To use this option pass the `--no-daemon` flag to the `prepare` command when preparing your physical device. Note that if you use this option while configuring a genesis node then you _must_ push configs while preparing the device by passing the `--push-configs` flag to the `prepare` command.

Since the node daemon is not installed on the device you will need to manually complete the steps normally done by the daemon.

1. After calling `up` on the deployment you must open the OpenVPN app on the device and connect to the VPN manually.
1. When calling `start` on the deployment you must manually open the RACE app on your device since RiB can't issue commands via the node daemon. Also note that RiB will not be able to view status of the device, but you will still be able to send and receive messages.

## Up the Deployment

Upping the deployment will start the VPN service that the deployment will use to network with the android device.
```
rib:2.0.0@code# rib deployment local up --name=example-bridged-deployment 
...

Stood Up Deployment: example-deployment
rib:2.0.0@code#
```
More information on the up command can be found [here](../reference/deployment/local/up.md)

## Connect Bridged Device

> :information_source: If you passed the `--push-configs` or `--no-daemon` flag to your `prepare` command please skip this step.

```
rib:2.0.0@code# rib deployment local bridged android connect --name=example-bridged-deployment
...

Connected Android device emulator-5554
```

If succesful you should be able to open the following address in a browser: `http://rib-file-server:8080`

> :information_source: One common issue is OpenVPN sometimes enables "Use system proxy". If you encounter trouble connect verify that "Use system proxy" is unchecked with OpenVPN settings. 

## Verify setup

You can verify that the device is communicating with RiB through the standard deployment status command:

```
1) rib:x.y.z@code# rib deployment local status -dd --name=example-bridged-deployment 
Deployment example-bridged-deployment apps are up
	race-client-00001: up
		app: installed
		daemon: started
	race-client-00002: up
		app: installed
		daemon: started
	race-client-00003: up
		app: installed
		daemon: started
	race-server-00001: up
		app: installed
		daemon: started
	race-server-00002: up
		app: installed
		daemon: started
	race-server-00003: up
		app: installed
		daemon: started
Deployment example-bridged-deployment container status is healthy
	race-client-00001: healthy
	race-client-00002: healthy
	race-server-00001: healthy
	race-server-00002: healthy
	race-server-00003: healthy
Deployment example-bridged-deployment services status is healthy
	ArtifactManager (PluginArtifactManagerTwoSixCpp): running
	RiB Services: healthy
		dnsproxy: healthy
		elasticsearch: healthy
		jaeger-collector: healthy
		jaeger-query: healthy
		kibana: healthy
		openvpn: healthy
		rib-file-server: healthy
		rib-redis: healthy
	Comms (twoSixIndirectCpp): running
```

## Testing

At this point testing is the same as the standard deployment. Please see [manual-deployment-test](../manual-deployment-test.md) for more information.

## Down

Deployments with Bridge mode are slightly different to Down. You will need to down the device first (disconnect from ADB, or close emulator). The you may down the deployment. If you down the deployment prior to downing the device, you will need to run `rib deployment local down --force` to down all the services.
