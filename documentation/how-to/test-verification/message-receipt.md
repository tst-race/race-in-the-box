# Manual Receipt Verification

This document defines the numerous ways to verify a message was successful.

## Checking  Logs on a Node

To validate a received message via logs, first go onto receiver node. Logs are located in `/log`. Recevied messages should appear in the `racetestapp.log`.

```
root@race-client-00002:/code# tail /log/racetestapp.log 
2022-01-19 22:41:00: INFO: Received message: checksum: 9d7dbde9932c78e2de065ba44ee463e065994744, size: 100, nonce: 10, from: race-client-00001, to: race-client-00002, test-id: default, sent-time: 1642632057408743, traceid: de454889d63e2b41, recv-time: 1642632060738666, message: default 0001 cHygb6eOInYYvInTpZXUd2xL5CUUiSpCotMnNkLbhzHhuXpCHatej83WZa60Qo5fgxILK29qy6bZyvPOswOVpfi
```

## Open Tracing

Open Tracing has a more detailed view of the message and the hops it took to reach the recipient node. Integration test events will use Open Tracing for verification so this should be the primary verification process.

With the deploment up, navigate to `http://<IP-Address>:16686/search`* in a browser. On the left hand side you should see a drop down labeled `Service` under which you should see all RACE nodes that are part of the deployment. Select the RACE node that sent the message and select `sendMessage` in the `Operation` dropdown. Click `Find Traces`. 

**IP-Address:** for local deployments use `127.0.0.1` as the ip address. For AWS deployments, use `rib env aws runtime-info` to find the cluster manager IP address and use that.

At this point you should see a trace on the right hand with the sender and receiver nodes listed under it. Click on the trace to get a more detailed view. This view is `Trace Timeline`. If you change the view using the dropdown in the top right of the dispay to `Trace Graph` it should be easier to see the path the message took from the sender to the recipient.