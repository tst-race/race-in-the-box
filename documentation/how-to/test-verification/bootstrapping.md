# Node Bootstrap Verification

This document defines the numerous ways to verify that a node was successfully
bootstrapped into the RACE network.

## Checking Application Status

If a node has been successfully bootstrapped, the app status for that node will
be `started` instead of `uninstalled`. If the app was installed but is not
running (e.g., it had bad configs or crashed) then the app status might be
`installed`.

```
1) rib:x.y.z@code# rib deployment status app --name=example-deployment -dd
Deployment bootstrap-android apps are partially started
	race-client-00001: started
		app: started
		daemon: started
	race-client-00002: up
		app: installed
		daemon: started
	race-client-00003: up
		app: uninstalled
		daemon: started
	race-server-00001: started
		app: started
		daemon: started
	race-server-00002: started
		app: started
		daemon: started
```

*See the [`rib deployment status app`](../../reference/deployment/status/app.md)
for additional details.*

## Checking Logs On Introducer Node

On the introducer node, the `race.log` file will contain a series of log
messages, starting a call to `prepareToBootstrap`. Search for this phrase and
look at the log messages that follow after it.

## Checking Logs On Bootstrapped Node

If the RACE app was installed on the bootstrapped node but did not run
correctly, examine the contents of the `race.log` file for any error messages.

## Sending Messages

To truly confirm that the node was successfully bootstrapped and is able to
communicate on the RACE network, send a message from the bootstrapped node to
a genesis node. Also, send a message from a genesis node to the bootstrapped
node.

*See the [message receipt verification](message-receipt.md) guide for additional
details.*
