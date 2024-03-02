# Send-Manual Message
Send a manual message across the deployment

## syntax

```
rib deployment <mode> message send-manual <args>
```

## Example

```
rib:2.0.0@code# rib deployment local message send-manual --name=example-deployment --message=hi
Sending Messages
Will send messages from the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003

Sent Messages To Deployment Nodes
rib:2.0.0@code#
```

## required args

#### --name TEXT
The name of the deployment to send messages on

#### --message TEXT
The message to send

## optional args

#### --recipient TEXT
*Default: All client nodes in deployment*
The node to send the message to. Must be a client node unless you are using network-manager-bypass

#### --sender TEXT
*Default: All client nodes in deployment*
The node to send the message from. Must be a client node unless you are using network-manager-bypass

#### --test-id TEXT
A string added to the message sent to aid in identification

#### --network-manager-bypass TEXT
Channel ID, link ID, or connection ID on which to send messages bypassing the network manager plugin (use '*' for any available channel)

#### --verify
Verify Receipt of Messages

#### --timeout INTEGER
Max time to wait for messages to be received
