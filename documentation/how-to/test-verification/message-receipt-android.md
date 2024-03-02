# Message Receipt Verification on Android

For Android nodes, you can verify messages using the [same methods](./message-receipt.md) as linux nodes but there are a couple additional things to check.

One thing to note is that Android logs are on the emulator, they get copied to the docker container to `/log` but there is a chance the service that runs that copy is broken. I

## Checking Logs on a Node

Android logs are on the emulator, they get copied to the docker container to `/log` but there is a chance the service that runs that copy is broken. So we should first check the logs as outlined [here](./message-receipt.md) and fallback to checking on the emulator if that fails.

To check on the emulator run the following on which ever node you want to check:
```
mac: user$ docker exec race-client-00002 bash
root@race-client-00002:/code# adb exec-out cat /storage/self/primary/Android/data/com.twosix.race/files/logs/racetestapp.log
```

## Viewing the UI

It is also possible to view the Android UI and verify/send messages from there. The process is slightly different for Local and AWS deployments

### Local Deployments

The VNC port (5901) is mapped to increasing port numbers starting at 35001 for race-client-00001 and incrementing by 1 for each client. To view the UI start a VNC viewer (CMD+K on Mac OS) after the deployment is up.

Enter `vnc://localhost:35001` for the VNC server. This should prompot you for a password which is "android".

At this point you may still interact with the Node via RiB but you can also click through the UI to manually send messages or validate received messages.