# Message Received Verification

This document demonstrates how to use the message verification feature `--verify` for both auto and manual message send commands

## General Information

Verification functionality can be optionally used with a send message command, to track if that batch of messages has been received successfully. The send message commands otherwise function the same as before. 

A particular `--timeout` value can be specified, otherwise the default of 30 seconds is used. If a `--test-id` is not specified, the system will create a unique one to be used instead. This is to assist with later manual verification if timeout occurs.

## Message Send-Auto

A longer `--timeout` value is recommended as the number of messages sent between each involved node, and the number of involved nodes increases. This is a useful way to check if/which nodes are successfully sending and receiving messages.

## Message Send-Manual

Since manual messaging allows for a user set `--message`, it can be a useful way to see if custom messages are being sent and received as expected. A longer `--timeout` value is recommended as the number of involved nodes increases.

## Using Verification

Have a deployment up and running, with nodes ready to send and receive messages. 

### How to use verification with an example send-auto call

This is multiple generated messages between all of the nodes:

```
rib:x.y.z@code# rib deployment local message send-auto --name=example-deployment --period=1 --quantity=5 --size=50 --verify --timeout=120

```

### How to use verification with an example send-manual call 

This is a single custom message between all of the nodes:

```
rib:x.y.z@code# rib deployment local message send-manual --name=example-deployment --message=TheLongestHelloWorldEver --verify --timeout=60

```
