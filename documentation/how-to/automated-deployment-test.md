# Automated Deployment Test

This document will walk through running an automated deployment test. For more information about how to test specific features, please see the other documents under [how-to](../how-to). For more information about specific commands and their options, please see the documentation under [reference](../reference)

## Create the Deployment
Create your deployment with the specific configuration you want to test. Please see more information on different deployment configuration options in [deployment-setup](./deployment-setup). The most simple example is [local-deployments](./deployment-setup/local-deployments.md)

```
rib:x.y.z@code# rib deployment local create --name=example-deployment --linux-client-count=3 --linux-server-count=3
Creating New Deployment: example-deployment
Network manager config gen status: complete, reason: success
Created New Deployment: example-deployment
rib:x.y.z@code#
```

## Run Deployment Test

```
rib:x.y.z@code# rib test deployment --name=example-deployment
```

Full example and output can be viewed [here](../reference/deployment/test/integrated.md)

The test evaluates success of message for you.

```
manual_messages Test Results:
	manual_messages Tests Passed: 6
	manual_messages Tests Failed: 0
auto_messages Test Results:
	auto_messages Tests Passed: 6
	auto_messages Tests Failed: 0
plugin_fatal Test Results:
	plugin_fatal Tests Passed: 6
	plugin_fatal Tests Failed: 0
```

## Run Channel Test

```
rib:x.y.z@code# rib test comms-channel --name=example-deployment --comms-channel=twoSixDirectCpp --comms-channel-type=s2s
```

Full example and output can be viewed [here](../reference/test/comms-channel.md)

The test evaluates success of message for you.

```
manual_messages Test Results:
	manual_messages Tests Passed: 6
	manual_messages Tests Failed: 0
auto_messages Test Results:
	auto_messages Tests Passed: 6
	auto_messages Tests Failed: 0
plugin_fatal Test Results:
	plugin_fatal Tests Passed: 6
	plugin_fatal Tests Failed: 0
```

## Advanced Usage Examples

### Bootstrapped Node As Introducer

In order to perform automated tests to bootstrap a node, then use that node to
bootstrap yet another node, a custom test plan must be specified via either the
`--test-plan-json` or `--test-plan` arguments. The `bootstrap_mapping` entry of
the test plan is a list of bootstrap mappings. They are executed in the order
they are defined, so the target of a bootstrap may be used as the introducer of
a subsequent bootstrap.

```
{
  "bootstrap_mapping": [
    {
      "architecture": "x86_64",
      "introducer": "race-client-00001",
      "target": "race-client-00002"
    },
    {
      "architecture": "x86_64",
      "introducer": "race-client-00002"
      "target": "race-client-00003"
    }
  ],
  ...
}
```

### Android Clients

Starting with 2.2.0, RiB can properly handle Android clients when performing
automated tests. There are a few caveats:

* If performing any bootstrapping with Android clients as the introducer, a
  suitable bootstrap channel must be included in the deployment.
* If any ARM bootstrapped Android clients are included in the deployment,
  the default test plan will not work. You must specify a custom test plan
  (either via `--test-plan-json` or `--test-plan`) in order to specify the
  architecture of the bootstrapped node as `arm64-v8a`.
* If using bridged Android clients, the test can only be executed against a
  running deployment with the `--running` option (or via the
  `test_config.is_running` parameter of the test plan JSON). This is because
  of the additional bridged device `prepare` and `connect` commands that must
  be run to properly set up the deployment for testing.

#### Managed Android Nodes

##### Genesis Managed Android Clients

```
1) rib:x.y.z@code# rib deployment local create --name=example-deployment \
    --android-client-count=1 ...
1) rib:x.y.z@code# rib deployment local test integrated --name=example-deployment
```

##### Bootstrapped Managed Android Clients

```
1) rib:x.y.z@code# rib deployment local create --name=example-deployment \
    --android-client-count=1 ...
1) rib:x.y.z@code# rib deployment local test integrated --name=example-deployment
```

*Note* If any of the non-genesis managed Android clients are ARM rather than
x86, then the test plan must be specified via either `--test-plan-json` or
`--test-plan` and specify the architecture of the bootstrapped node as
`arm64-v8a`. See the [Bootstrapped Bridged Android Clients](#bootstrapped-bridged-android-clients)
example below for an example of the required test plan JSON.

#### Bridged Android Nodes

When testing a deployment with bridged Android clients, the deployment must be
manually started and the automated tests must be run with the `--running` option
(or with the `test_config.is_running` parameter set to `true` in the test plan
JSON). This is because of the additional bridged device `prepare` and `connect`
commands that must be run to properly set up the deployment for testing.

##### Genesis Bridged Android Clients

All genesis bridged Android clients in a deployment must be properly set up via
the [`bridged android prepare`](../reference/deployment/bridged/android/prepare.md)
and [`bridged android connect`](../reference/deployment/bridged/android/connect.md)
commands prior to running the test.

```
# Create the deployment
1) rib:x.y.z@code# rib deployment local create --name=example-deployment \
    --android-client-count=1 --android-client-bridge-count=1 ...

# Set up deployment
1) rib:x.y.z@code# rib deployment local bridged android prepare \
    --name=example-deployment --persona=race-client-00003
1) rib:x.y.z@code# rib deployment local up --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android connect --name=example-deployment
1) rib:x.y.z@code# rib deployment local start --name=example-deployment

# Execute test against running deployment
1) rib:x.y.z@code# rib deployment local test integrated --name=example-deployment --running

# Clean up deployment
1) rib:x.y.z@code# rib deployment local stop --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android disconnect --name=example-deployment
1) rib:x.y.z@code# rib deployment local down --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android unprepare --name=example-deployment
```

##### Bootstrapped Bridged Android Clients

When testing a deployment with bridged Android clients, the deployment must be
manually started and the automated tests must be run with the `--running` option
(or with the `test_config.is_running` parameter set to `true` in the test plan
JSON). This is because of the additional bridged device `prepare` and `connect`
commands that must be run to properly set up the deployment for testing.

*Note* When bootstrapping a physical bridged Android device (i.e., its
architecture is ARM), the test plan must be specified via either
`--test-plan-json` or `--test-plan` and specify the architecture of the
bootstrapped node as `arm64-v8a`. The
[`test generate-plan`](../reference/deployment/test/generate-plan.md) command
can be used to generate the default test plan JSON for modification.

```
{
  "bootstrap_mapping": [
    {
      "architecture": "arm64-v8a",
      "introducer": "race-client-00001",
      "target": "race-client-00003"
    }
  ],
  ...
  "test_config": {
    "is_running": true,
  }
}
```

*Note* It is important to use the `--allow-silent-installs` option when
preparing any bridged Android device that will be bootstrapped as part of the
test. Otherwise, manual intervention will be needed to complete the RACE app
installation.

```
# Create the deployment
1) rib:x.y.z@code# rib deployment local create --name=example-deployment \
    --android-client-count=1 --android-client-bridge-count=1 \
	--android-client-uninstalled-count=1 ...

# Set up deployment
1) rib:x.y.z@code# rib deployment local bridged android prepare \
    --name=example-deployment --persona=race-client-00003 --allow-silent-installs
1) rib:x.y.z@code# rib deployment local up --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android connect --name=example-deployment
1) rib:x.y.z@code# rib deployment local start --name=example-deployment

# Execute test against running deployment
1) rib:x.y.z@code# rib deployment local test integrated \
    --name=example-deployment --running --test-plan=/path/to/test-plan.json

# Clean up deployment
1) rib:x.y.z@code# rib deployment local stop --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android disconnect --name=example-deployment
1) rib:x.y.z@code# rib deployment local down --name=example-deployment
1) rib:x.y.z@code# rib deployment local bridged android unprepare --name=example-deployment
```
