# Send-Auto Message
Send a series of generated messages across the deployment. The deployment must be up to use this command.

## syntax

```
rib deployment <mode> message send-auto <args>
```

## Example

```
rib:x.y.z@code# rib deployment local message send-auto --name=example-deployment --period=10 --quantity=5 --size=10
Sending Messages
Will send messages from the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003

Sent Messages To Deployment Nodes
rib:x.y.z@code#
```

## required args

#### --name TEXT
The name of the deployment to send messages on

#### --period TEXT
Time (in milliseconds) to wait between sending messages

#### --quantity INTEGER
Quantity of messages to send

#### --size INTEGER
Size (in bytes) of messages to send

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

