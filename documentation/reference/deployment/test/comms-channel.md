# comms-channel Test

This document will walk through automated comms-channel tests in RiB.

## syntax

```
rib deployment <mode> test comms-channel <args>
```

## Example

```
rib:x.y.z@code# rib deployment local test comms-channel --name=example-deployment --comms-channel=twoSixDirectCpp --comms-channel-type=s2s
Using default RiB mode: local
Testing Comms Channel: twoSixDirectCpp (deployment = example-deployment, test-plan = None)
Running Setup Steps
Standing Up Deployment
Current status:
	0/6 nodes are unknown
	6/6 nodes are down
	0/6 nodes are up
	0/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	8/8 services are down
	0/8 services are up

Will stand up the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Comms (twoSixIndirectCpp) Start External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Start External Services
Waiting for 6 nodes to stand up.......done
Current status:
	0/6 nodes are unknown
	0/6 nodes are down
	0/6 nodes are up
	6/6 nodes are installed
	0/6 nodes are started
	0/8 services are unknown
	1/8 services are down
	7/8 services are up

Waiting 0 seconds before starting nodes to allow for external services and race nodes containers to properly start
Deleting Logs
Will delete logs the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Starting Deployment
Creating configs archive
Will start the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to start...done
Waiting 15 seconds before executing tests to allow for nodes to initialize and network to stabilize
Running Test Steps
Running Test Steps: manual_messages
Will send messages from the following nodes:
	race-server-00001

Will send messages from the following nodes:
	race-server-00003

Will send messages from the following nodes:
	race-server-00001

Will send messages from the following nodes:
	race-server-00002

Will send messages from the following nodes:
	race-server-00002

Will send messages from the following nodes:
	race-server-00003

Running Test Steps: auto_messages
Will send messages from the following nodes:
	race-server-00001

Will send messages from the following nodes:
	race-server-00003

Will send messages from the following nodes:
	race-server-00001

Will send messages from the following nodes:
	race-server-00002

Will send messages from the following nodes:
	race-server-00002

Will send messages from the following nodes:
	race-server-00003

Running Test Steps: plugin_fatal
Sleeping for 60 seconds (Test takes time to run)
Running Evaluation Steps
Will backup logs the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to backup log files...
Done waiting for node log files
Running Eval Steps: manual_messages
Running Eval Steps: auto_messages
Running Eval Steps: plugin_fatal
Stopping test. Tearing down deployment
Test Teardown: Running Teardown Steps
Test Teardown: Stopping Deployment
Will stop the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to stop....done
Test Teardown: Deployment has been stopped
Test Teardown: Downing Deployment
Will tear down the following nodes:
	race-client-00001
	race-client-00002
	race-client-00003
	race-server-00001
	race-server-00002
	race-server-00003

Waiting for 6 nodes to tear down...done
Comms (twoSixIndirectCpp) Stop External Services
ArtifactManager (PluginArtifactManagerTwoSixCpp) Stop External Services
Test Teardown: Deployment has been downed
Test Details:
	deployment_name: example-deployment
	network manager plugin in deployment: PluginNMTwoSixStub
	comms channels in deployment: ['twoSixDirectCpp', 'twoSixIndirectCpp']
	clients: ['race-client-00001', 'race-client-00002', 'race-client-00003']
	servers: ['race-server-00001', 'race-server-00002', 'race-server-00003']
	run_time: 60
	delay_start: 0
	delay_execute: 15
	is_running: False
	no_down: False
	network_manager_bypass: True
	comms_channel being tested: twoSixDirectCpp
	comms_channel_type being tested: s2s
manual_messages Test Results:
	manual_messages Tests Passed: 6
	manual_messages Tests Failed: 0
auto_messages Test Results:
	auto_messages Tests Passed: 6
	auto_messages Tests Failed: 0
plugin_fatal Test Results:
	plugin_fatal Tests Passed: 6
	plugin_fatal Tests Failed: 0

rib:x.y.z@code#
```

## required args

#### `--name TEXT`

The name of the deployment to test

#### `--comms-channel TEXT`

The name of the comms-channel to test

#### `--comms-channel-type [c2c|s2s|all]`

The type of connections the channel supports. 

## optional args

#### `--test-plan TEXT`
Path to a test plan file (relative to /code/ directory)

#### `----test-plan-json TEXT`
The test plan in escaped JSON

#### `--run-time INTEGER`
Time (seconds) to allow test to run [0<=x<=3600]

#### `--running`
Use an already running deployment

#### `--delay-execute INTEGER`
Time (seconds) after starting nodes before running tests [0<=x<=3600]

#### `--delay-start INTEGER`
Time (seconds) after upping nodes before starting nodes [0<=x<=3600]

#### `--delay-evaluation INTEGER`
Time (seconds) after starting nodes before first evaluation attempt [0<=x<=3600]. Evaluation will 
retry continuously until the runtime is complete or if the evaulation is successful.

#### `--evaluation-interval INTEGER`
Time (seconds) to wait between attempts to validate test  [0<=x<=3600]

#### `--raise-on-fail`
Raise Exception on failure

#### `--debug`
Keep the deployment running after the test to allow debugging

#### `--no-down`
Prevent the deployment from being downed to allow debugging the deployment?




