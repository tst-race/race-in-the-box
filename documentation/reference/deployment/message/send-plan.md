# Send-Plan of Messages
Send a messages across the deployment based on a given plan

## syntax

```
rib deployment <mode> message send-plan <args>
```

## Example

```
rib:2.0.0@code# rib deployment local message send-plan --name=example-deployment --plan-file=/code/plan-file.json 
Sending Test Plan
Will send messages from the following nodes:
	race-client-00001

Sent Messages To Deployment Nodes
rib:2.0.0@code#
```

## required args

#### --name TEXT
The name of the deployment to send messages on

#### --plan-file TEXT
The path to the plan file within RiB's filesystem (Specify `--code` with your RiB to volume mount a directory from your host machine to `/code` in RiB)

## optional args

#### --start-time INTEGER
The time the messages will start to send, in
                        milliseconds since epoch

#### --test-id TEXT
A string added to the message sent to aid in identification

#### --network-manager-bypass TEXT
Channel ID, link ID, or connection ID on which to send messages bypassing the network manager plugin (use '*' for any available channel)
